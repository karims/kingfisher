"""CLI for MVIR golden regression checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from mvir.cli.formalize import build_provider, format_cli_exception
from mvir.extract.formalize import formalize_text_to_mvir


def _canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _canonicalize(val) for key, val in sorted(value.items())}
    if isinstance(value, list):
        normalized = [_canonicalize(item) for item in value]
        return sorted(
            normalized,
            key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False),
        )
    return value


def _normalize_for_compare(payload: dict[str, Any]) -> dict[str, Any]:
    data = json.loads(json.dumps(payload))
    meta = data.get("meta")
    if isinstance(meta, dict):
        meta.pop("created_at", None)
    return _canonicalize(data)


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
        "--fail-fast",
        action="store_true",
        help="Stop after first mismatch/failure.",
    )
    args = parser.parse_args(argv)

    try:
        provider = build_provider(
            args.provider,
            mock_path=args.mock_path,
            openai_format=args.openai_format,
            openai_allow_fallback=args.openai_allow_fallback,
        )
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {format_cli_exception(exc)}")
        return 1

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"ERROR: input dir not found: {input_dir}")
        return 1

    files = sorted(input_dir.rglob("*.json"))
    if not files:
        print(f"ERROR: no JSON files found under {input_dir}")
        return 1

    mismatches: list[str] = []
    failures: list[str] = []

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
                temperature=args.temperature,
                strict=args.strict,
            )
            rerun_payload = rerun_mvir.model_dump(by_alias=False, exclude_none=True)

            left = _normalize_for_compare(payload)
            right = _normalize_for_compare(rerun_payload)
            if left != right:
                mismatches.append(str(path))
                print(f"MISMATCH: {path}")
                if args.fail_fast:
                    break
            else:
                print(f"OK: {path}")
        except Exception as exc:  # noqa: BLE001 - per-file boundary
            failures.append(f"{path}: {format_cli_exception(exc)}")
            print(f"ERROR: {path}: {format_cli_exception(exc)}")
            if args.fail_fast:
                break

    total = len(files)
    print(f"total={total} mismatches={len(mismatches)} failed={len(failures)}")
    if mismatches:
        print("mismatch files:")
        for item in mismatches:
            print(item)
    if failures:
        print("failed files:")
        for item in failures:
            print(item)

    if mismatches or failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
