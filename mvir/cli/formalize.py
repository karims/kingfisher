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
    args = parser.parse_args(argv)

    try:
        text_path = Path(args.path)
        text = text_path.read_text(encoding="utf-8")
        problem_id = text_path.stem
        openai_format = args.openai_format
        if args.provider == "openai" and openai_format is None:
            openai_format = "json_object"

        provider = build_provider(
            args.provider,
            mock_path=args.mock_path,
            openai_format=openai_format or "json_object",
            openai_allow_fallback=args.openai_allow_fallback,
        )

        mvir = formalize_text_to_mvir(
            text,
            provider,
            problem_id=problem_id,
            temperature=args.temperature,
            strict=args.strict,
            debug_dir=args.debug_dir,
        )
        if not args.strict:
            grounding_errors = validate_grounding_contract(mvir)
            if grounding_errors:
                print("WARNING: Grounding contract failed: " + "; ".join(grounding_errors))

        payload = mvir.model_dump(by_alias=False, exclude_none=True)

        if args.out:
            Path(args.out).write_text(
                json.dumps(payload, indent=2), encoding="utf-8"
            )
        if args.print_json:
            print(json.dumps(payload, ensure_ascii=False))

        print(f"OK: {problem_id}")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {format_cli_exception(exc)}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
