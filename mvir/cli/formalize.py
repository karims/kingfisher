"""CLI entrypoint for Phase 3 formalization.

Preprocess is lossless + offsets only; no semantic classification.
Phase 3 uses an LLM to produce MVIR semantics.
Providers must not modify MVIR schema.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mvir.extract.contract import validate_grounding_contract
from mvir.extract.formalize import formalize_text_to_mvir
from mvir.extract.provider_base import LLMProvider, ProviderError
from mvir.extract.providers.mock import MockProvider
from mvir.extract.providers.openai_provider import OpenAIProvider
from mvir.preprocess.context import build_preprocess_output
from mvir.render.bundle import write_explain_bundle
from mvir.render.markdown import render_mvir_markdown
from mvir.trace import TraceLogger, new_event


def _configure_provider_sampling(provider: object) -> None:
    """Best-effort OpenAI sampling defaults for lower-variance runs."""

    if getattr(provider, "name", None) != "openai":
        return
    try:
        current_top_p = getattr(provider, "top_p", None)
        if current_top_p is None:
            setattr(provider, "top_p", 1.0)
    except Exception:
        return


def build_provider(
    provider_name: str,
    *,
    mock_path: str | None = None,
    openai_format: str = "json_object",
    openai_allow_fallback: bool = False,
) -> LLMProvider:
    """Construct a provider instance from CLI arguments."""

    if provider_name == "mock":
        if not mock_path:
            raise ValueError("--mock-path is required for mock provider.")
        mapping = json.loads(Path(mock_path).read_text(encoding="utf-8"))
        return MockProvider(mapping)
    if provider_name == "openai":
        return OpenAIProvider(
            format_mode=openai_format,
            allow_fallback=openai_allow_fallback,
        )
    raise ValueError(f"Unsupported provider: {provider_name}")


def format_cli_exception(exc: Exception) -> str:
    """Return a user-facing CLI error message."""

    if isinstance(exc, ProviderError):
        if exc.kind == "bad_schema":
            return (
                "OpenAI rejected the json_schema (unsupported schema feature). "
                "Use skeleton schema or --openai-format json_object."
            )

        msg = str(exc)
        lower = msg.lower()
        if (
            "json_schema" in lower
            and (
                "not supported" in lower
                or "unsupported" in lower
                or "does not support" in lower
            )
        ):
            return (
                "OpenAI model does not support json_schema enforcement. "
                "Use --openai-format json_object or --openai-allow-fallback."
            )
    return str(exc)


def _default_md_out_path(json_out_path: str) -> Path:
    """Return the default Markdown output path for a JSON output path."""

    return Path(json_out_path).with_suffix(".md")


def _resolve_md_out_path(
    *,
    render_md: bool,
    json_out: str | None,
    md_out: str | None,
) -> Path | None:
    """Resolve Markdown output path when markdown rendering is enabled."""

    if not render_md:
        return None
    if not json_out:
        raise ValueError("--render-md requires --out (Markdown is emitted in addition to JSON).")
    if md_out:
        return Path(md_out)
    return _default_md_out_path(json_out)


def _write_markdown_report(mvir, md_path: Path) -> None:
    """Write a Markdown report for an MVIR object."""

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_mvir_markdown(mvir), encoding="utf-8")


class _SafeTraceLogger:
    """Best-effort trace logger that never raises to CLI flow."""

    def __init__(self, path: Path) -> None:
        self._logger: TraceLogger | None = None
        self._enabled = True
        try:
            self._logger = TraceLogger(str(path))
        except Exception as exc:
            self._enabled = False
            print(f"WARNING: solver trace logging disabled: {exc}")

    def append(self, event: dict) -> None:
        if not self._enabled or self._logger is None:
            return
        try:
            self._logger.append(event)
        except Exception as exc:
            self._enabled = False
            print(f"WARNING: solver trace logging failed: {exc}")

    def flush(self) -> None:
        if not self._enabled or self._logger is None:
            return
        try:
            self._logger.flush()
        except Exception as exc:
            self._enabled = False
            print(f"WARNING: solver trace flush failed: {exc}")

    def close(self) -> None:
        if self._logger is None:
            return
        try:
            self._logger.close()
        except Exception as exc:
            print(f"WARNING: solver trace close failed: {exc}")


def main(argv: list[str] | None = None) -> int:
    """Run the formalization CLI."""

    parser = argparse.ArgumentParser(description="Formalize text into MVIR JSON.")
    parser.add_argument("path", help="Path to problem text file.")
    parser.add_argument(
        "--provider",
        choices=["mock", "openai"],
        default="mock",
        help="Provider name.",
    )
    parser.add_argument(
        "--mock-path", help="Path to mock provider response mapping JSON."
    )
    parser.add_argument("--out", help="Output path for MVIR JSON.")
    parser.add_argument(
        "--render-md",
        action="store_true",
        help="Also render a Markdown report from the validated MVIR output.",
    )
    parser.add_argument(
        "--md-out",
        help="Markdown output path (default: same as --out but .md extension).",
    )
    parser.add_argument(
        "--bundle-dir",
        help=(
            "Optional directory to write explain bundle on success "
            "(writes to <bundle-dir>/<meta.id>/)."
        ),
    )
    parser.add_argument(
        "--print",
        dest="print_json",
        action="store_true",
        help="Print MVIR JSON to stdout.",
    )
    parser.add_argument(
        "--strict",
        dest="strict",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enforce grounding-contract failures as errors (default: true).",
    )
    parser.add_argument(
        "--openai-format",
        choices=["json_schema", "json_object"],
        default=None,
        help=(
            "OpenAI output format mode. OpenAI has schema limitations; "
            "json_object is recommended for stability. "
            "Use json_schema only when explicitly needed."
        ),
    )
    parser.add_argument(
        "--openai-allow-fallback",
        action="store_true",
        help=(
            "If strict schema is rejected, automatically retry with json_object + "
            "JSON-only instruction."
        ),
    )
    parser.add_argument(
        "--debug-dir",
        help="Optional directory to write debug bundles for failed extractions.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature for provider calls (default: 0.0).",
    )
    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Force deterministic sampling settings (temperature=0 for this run).",
    )
    parser.add_argument(
        "--allow-degraded",
        action="store_true",
        help="Allow degraded output by dropping/replacing invalid expressions with warnings.",
    )
    args = parser.parse_args(argv)
    trace_logger: _SafeTraceLogger | None = None

    try:
        text_path = Path(args.path)
        text = text_path.read_text(encoding="utf-8")
        problem_id = text_path.stem
        if args.debug_dir:
            trace_path = Path(args.debug_dir) / f"{problem_id}.solver_trace.jsonl"
            trace_logger = _SafeTraceLogger(trace_path)
        if trace_logger is not None:
            trace_logger.append(
                new_event(
                    "note",
                    "start: read source",
                    data={"problem_id": problem_id, "source_path": str(text_path)},
                )
            )
            preprocess_out = build_preprocess_output(text)
            trace_logger.append(
                new_event(
                    "transform",
                    "after preprocess spans",
                    data={"span_count": len(preprocess_out.spans)},
                )
            )
        openai_format = args.openai_format
        if args.provider == "openai" and openai_format is None:
            openai_format = "json_object"

        provider = build_provider(
            args.provider,
            mock_path=args.mock_path,
            openai_format=openai_format or "json_object",
            openai_allow_fallback=args.openai_allow_fallback,
        )
        _configure_provider_sampling(provider)
        call_temperature = 0.0 if args.deterministic else args.temperature

        mvir = formalize_text_to_mvir(
            text,
            provider,
            problem_id=problem_id,
            temperature=call_temperature,
            strict=args.strict,
            debug_dir=args.debug_dir,
            degrade_on_validation_failure=args.openai_allow_fallback,
            deterministic=args.deterministic,
            allow_degraded=args.allow_degraded,
        )
        if trace_logger is not None:
            trace_logger.append(
                new_event(
                    "tool_result",
                    "after provider response received",
                    data={"provider": args.provider},
                )
            )
            repair_warning_codes = {
                "invalid_assumption_expr_dropped",
                "invalid_goal_expr_replaced",
                "invalid_goal_target_expr_dropped",
                "goal_kind_downgraded",
                "dropped_expr",
                "degraded_output",
            }
            repair_codes = [
                w.code for w in mvir.warnings if w.code in repair_warning_codes
            ]
            if repair_codes:
                trace_logger.append(
                    new_event(
                        "transform",
                        "after repair",
                        data={"warning_codes": sorted(set(repair_codes))},
                    )
                )
            trace_logger.append(
                new_event(
                    "final",
                    "after MVIR validated",
                    data={"mvir_id": mvir.meta.id},
                )
            )
        if not args.strict:
            grounding_errors = validate_grounding_contract(mvir)
            if grounding_errors:
                print("WARNING: Grounding contract failed: " + "; ".join(grounding_errors))

        payload = mvir.model_dump(by_alias=False, exclude_none=True)
        md_path = _resolve_md_out_path(
            render_md=args.render_md,
            json_out=args.out,
            md_out=args.md_out,
        )

        if args.out:
            Path(args.out).write_text(
                json.dumps(payload, indent=2), encoding="utf-8"
            )
        if md_path is not None:
            _write_markdown_report(mvir, md_path)
        if args.bundle_dir:
            bundle_path = Path(args.bundle_dir) / mvir.meta.id
            write_explain_bundle(mvir, bundle_path)
        if args.print_json:
            print(json.dumps(payload, ensure_ascii=False))
        if trace_logger is not None:
            trace_logger.append(
                new_event(
                    "final",
                    "final: wrote output path",
                    data={"out": args.out, "md_out": str(md_path) if md_path else None},
                )
            )
            trace_logger.flush()

        print(f"OK: {problem_id}")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {format_cli_exception(exc)}")
        return 1
    finally:
        if trace_logger is not None:
            trace_logger.close()


if __name__ == "__main__":
    raise SystemExit(main())
