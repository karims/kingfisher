"""CLI for MVIR golden regression checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from mvir.cli.formalize import build_provider, format_cli_exception
from mvir.core.ast import expr_to_dict, parse_expr
from mvir.core.ast_normalize import normalize_expr_dict
from mvir.extract.formalize import formalize_text_to_mvir


def _canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _canonicalize(val) for key, val in sorted(value.items())}
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    return value


def _canonical_expr(expr: Any) -> Any:
    if not isinstance(expr, dict):
        return expr
    normalized = normalize_expr_dict(expr)
    try:
        return _canonicalize(expr_to_dict(parse_expr(normalized)))
    except Exception:  # noqa: BLE001 - best-effort canonicalization
        return _canonicalize(normalized)


def _trace_key(trace: Any) -> str:
    if not isinstance(trace, list):
        return ""
    return ",".join(item for item in trace if isinstance(item, str))


def _normalize_for_compare(payload: dict[str, Any], *, drop_generator: bool = True) -> dict[str, Any]:
    data = json.loads(json.dumps(payload))
    meta = data.get("meta")
    if isinstance(meta, dict):
        meta.pop("created_at", None)
        if drop_generator:
            meta.pop("generator", None)

    entities = data.get("entities")
    if isinstance(entities, list):
        data["entities"] = sorted(
            (_canonicalize(item) for item in entities),
            key=lambda item: item.get("id", "") if isinstance(item, dict) else "",
        )

    assumptions = data.get("assumptions")
    if isinstance(assumptions, list):
        canonical_assumptions: list[dict[str, Any]] = []
        for item in assumptions:
            if not isinstance(item, dict):
                continue
            current = _canonicalize(item)
            if "expr" in current:
                current["expr"] = _canonical_expr(current.get("expr"))
            canonical_assumptions.append(current)
        data["assumptions"] = sorted(
            canonical_assumptions,
            key=lambda item: (
                item.get("kind", ""),
                _trace_key(item.get("trace")),
                json.dumps(item.get("expr"), sort_keys=True, ensure_ascii=False),
            ),
        )

    concepts = data.get("concepts")
    if isinstance(concepts, list):
        data["concepts"] = sorted(
            (_canonicalize(item) for item in concepts),
            key=lambda item: item.get("id", "") if isinstance(item, dict) else "",
        )

    warnings = data.get("warnings")
    if isinstance(warnings, list):
        data["warnings"] = sorted(
            (_canonicalize(item) for item in warnings),
            key=lambda item: (
                item.get("code", "") if isinstance(item, dict) else "",
                _trace_key(item.get("trace")) if isinstance(item, dict) else "",
                item.get("message", "") if isinstance(item, dict) else "",
            ),
        )

    trace = data.get("trace")
    if isinstance(trace, list):
        data["trace"] = sorted(
            (_canonicalize(item) for item in trace),
            key=lambda item: item.get("span_id", "") if isinstance(item, dict) else "",
        )

    goal = data.get("goal")
    if isinstance(goal, dict):
        goal = _canonicalize(goal)
        if "expr" in goal:
            goal["expr"] = _canonical_expr(goal.get("expr"))
        if "target" in goal:
            goal["target"] = _canonical_expr(goal.get("target"))
        data["goal"] = goal

    return _canonicalize(data)


def _is_baseline_file(path: Path) -> bool:
    name = path.name
    return (
        name.endswith(".json")
        and not name.endswith(".json_object.json")
        and not name.endswith(".json_schema.json")
    )


def _configure_provider_for_golden(provider: object) -> None:
    """Best-effort deterministic provider config for golden runs."""

    # Golden should be deterministic across reruns; this is safe no-op for non-openai providers.
    if getattr(provider, "name", None) != "openai":
        return
    try:
        current_top_p = getattr(provider, "top_p", None)
        if current_top_p is None:
            setattr(provider, "top_p", 1.0)
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    """Run golden regression over JSON files in out/mvir."""

    parser = argparse.ArgumentParser(
        description="Re-run MVIR formalization and compare against golden JSON outputs."
    )
    parser.add_argument(
        "--input-dir",
        default="out/mvir",
        help="Directory containing baseline MVIR .json files (default: out/mvir).",
    )
    parser.add_argument(
        "--provider",
        choices=["mock", "openai"],
        default="openai",
        help="Provider backend to re-run formalization.",
    )
    parser.add_argument(
        "--mock-path",
        help="Path to mock provider mapping JSON (required when --provider mock).",
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
        default="json_object",
        help="OpenAI output format mode.",
    )
    parser.add_argument(
        "--openai-allow-fallback",
        action="store_true",
        help="Allow OpenAI fallback from json_schema to json_object when needed.",
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
        "--fail-fast",
        action="store_true",
        help="Stop after first mismatch/failure.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Overwrite baseline with canonical rerun output when a mismatch is found.",
    )
    parser.add_argument(
        "--fail-on-mismatch",
        action="store_true",
        help="Return non-zero when mismatches are detected.",
    )
    args = parser.parse_args(argv)

    try:
        provider = build_provider(
            args.provider,
            mock_path=args.mock_path,
            openai_format=args.openai_format,
            openai_allow_fallback=args.openai_allow_fallback,
        )
        _configure_provider_for_golden(provider)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {format_cli_exception(exc)}")
        return 1

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"ERROR: input dir not found: {input_dir}")
        return 1
    new_dir = input_dir / ".new"
    debug_dir = input_dir / ".debug"
    new_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(path for path in input_dir.rglob("*.json") if _is_baseline_file(path))
    if not files:
        print(f"ERROR: no JSON files found under {input_dir}")
        return 1

    mismatches: list[str] = []
    failures: list[str] = []
    degraded: list[str] = []
    variant = (
        f"{args.openai_format}{'+fallback' if args.openai_allow_fallback else ''}"
        if args.provider == "openai"
        else args.provider
    )

    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            source = payload.get("source")
            meta = payload.get("meta")
            if not isinstance(source, dict) or not isinstance(source.get("text"), str):
                raise ValueError("Missing source.text in baseline JSON.")
            problem_id = (
                meta.get("id")
                if isinstance(meta, dict) and isinstance(meta.get("id"), str)
                else path.stem
            )
            rerun_mvir = formalize_text_to_mvir(
                source["text"],
                provider,
                problem_id=problem_id,
                temperature=0.0 if args.deterministic else args.temperature,
                strict=args.strict,
                degrade_on_validation_failure=True,
                deterministic=args.deterministic,
            )
            rerun_payload = rerun_mvir.model_dump(by_alias=False, exclude_none=True)
            warning_codes: set[str] = set()
            warnings = rerun_payload.get("warnings")
            if isinstance(warnings, list):
                for item in warnings:
                    if isinstance(item, dict):
                        code = item.get("code")
                        if isinstance(code, str):
                            warning_codes.add(code)
            if warning_codes & {
                "invalid_assumption_expr_dropped",
                "invalid_goal_expr_replaced",
                "invalid_mvir_recovered",
                "grounding_contract_degraded",
            }:
                degraded.append(str(path))

            left = _normalize_for_compare(payload)
            right = _normalize_for_compare(rerun_payload)
            if left != right:
                mismatches.append(str(path))
                new_path = new_dir / path.name
                new_path.write_text(
                    json.dumps(right, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                if args.update:
                    path.write_text(
                        json.dumps(right, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    print(f"UPDATE: {path} (variant={variant}, new={new_path})")
                else:
                    print(f"MISMATCH: {path} (variant={variant}, new={new_path})")
                if args.fail_fast:
                    break
            else:
                print(f"OK: {path}")
        except Exception as exc:  # noqa: BLE001 - per-file boundary
            failures.append(f"{path}: {format_cli_exception(exc)}")
            print(f"ERROR: {path}: {format_cli_exception(exc)}")
            failed_artifact = debug_dir / f"{path.stem}.failed.json"
            failed_artifact.write_text(
                json.dumps(
                    {
                        "baseline_path": str(path),
                        "variant": variant,
                        "error": format_cli_exception(exc),
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            print(f"FAILED_ARTIFACT: {failed_artifact}")
            if args.fail_fast:
                break

    total = len(files)
    print(
        f"total={total} mismatches={len(mismatches)} failed={len(failures)} degraded={len(degraded)}"
    )
    if mismatches:
        print("mismatch files:")
        for item in mismatches:
            print(item)
    if failures:
        print("failed files:")
        for item in failures:
            print(item)
    if degraded:
        print("degraded files:")
        for item in degraded:
            print(item)

    if failures:
        return 1
    if mismatches and args.fail_on_mismatch:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
