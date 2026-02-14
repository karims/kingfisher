"""CLI for directory-based formalization."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from mvir.cli.formalize import build_provider, format_cli_exception
from mvir.extract.cache import ResponseCache
from mvir.extract.contract import validate_grounding_contract
from mvir.extract.formalize import formalize_text_to_mvir
from mvir.extract.report import RunReport, classify_exception


def main(argv: list[str] | None = None) -> int:
    """Run directory-level formalization pipeline."""

    parser = argparse.ArgumentParser(description="Formalize all .txt files in a directory.")
    parser.add_argument("input_dir", help="Root directory containing problem .txt files.")
    parser.add_argument(
        "--provider",
        choices=["mock", "openai"],
        default="mock",
        help="Provider backend.",
    )
    parser.add_argument(
        "--mock-path",
        help="Path to JSON mapping used by mock provider.",
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        help="Directory to write MVIR JSON files.",
    )
    parser.add_argument(
        "--cache-dir",
        help="Enable file cache at this directory.",
    )
    parser.add_argument(
        "--report",
        help="Optional JSON report output path.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after first failure and return non-zero.",
    )
    parser.add_argument(
        "--strict",
        dest="strict",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enforce grounding-contract failures as errors (default: true).",
    )
    parser.add_argument(
        "--debug-dir",
        help="Optional directory to write per-problem debug bundles on failure.",
    )
    parser.add_argument(
        "--openai-format",
        choices=["json_schema", "json_object"],
        default="json_schema",
        help=(
            "OpenAI output format mode: json_schema = strict enforcement (may be rejected), "
            "json_object = JSON-only output (recommended)."
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
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature for provider calls (default: 0.0).",
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
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache = ResponseCache(args.cache_dir) if args.cache_dir else None

    files = sorted(input_dir.rglob("*.txt"))
    total = len(files)
    run_report = RunReport()

    for path in files:
        problem_id = path.stem
        try:
            text = path.read_text(encoding="utf-8")
            mvir = formalize_text_to_mvir(
                text,
                provider,
                problem_id=problem_id,
                temperature=args.temperature,
                cache=cache,
                use_cache=True,
                strict=args.strict,
                debug_dir=args.debug_dir,
            )
            payload = mvir.model_dump(by_alias=False, exclude_none=True)
            (out_dir / f"{problem_id}.json").write_text(
                json.dumps(payload, indent=2),
                encoding="utf-8",
            )
            run_report.ok.append(problem_id)
            if not args.strict:
                grounding_errors = validate_grounding_contract(mvir)
                if grounding_errors:
                    failure = {
                        "id": problem_id,
                        "kind": "grounding_contract",
                        "message": "; ".join(grounding_errors),
                    }
                    if args.debug_dir:
                        failure["debug_path"] = str(Path(args.debug_dir) / problem_id)
                    run_report.failed.append(failure)
                    if args.fail_fast:
                        break
        except Exception as exc:  # noqa: BLE001 - per-item fault isolation
            print(f"ERROR [{problem_id}]: {format_cli_exception(exc)}")
            kind, message = classify_exception(exc)
            failure = {"id": problem_id, "kind": kind.value, "message": message}
            if args.debug_dir:
                failure["debug_path"] = str(Path(args.debug_dir) / problem_id)
            run_report.failed.append(failure)
            if args.fail_fast:
                break

    failed = len(run_report.failed)
    ok = len(run_report.ok)
    failure_kinds = Counter(item["kind"] for item in run_report.failed)

    print(f"total={total} ok={ok} failed={failed}")
    if failure_kinds:
        print("top failure kinds:")
        for kind, count in failure_kinds.most_common():
            print(f"- {kind}: {count}")
    else:
        print("top failure kinds: none")

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_payload = {"ok": run_report.ok, "failed": run_report.failed}
        report_path.write_text(
            json.dumps(report_payload, indent=2),
            encoding="utf-8",
        )

    if args.fail_fast and failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
