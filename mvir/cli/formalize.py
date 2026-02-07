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
from mvir.extract.providers.mock import MockProvider


def main(argv: list[str] | None = None) -> int:
    """Run the formalization CLI."""

    parser = argparse.ArgumentParser(description="Formalize text into MVIR JSON.")
    parser.add_argument("path", help="Path to problem text file.")
    parser.add_argument("--provider", default="mock", help="Provider name.")
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
    args = parser.parse_args(argv)

    try:
        text_path = Path(args.path)
        text = text_path.read_text(encoding="utf-8")
        problem_id = text_path.stem

        if args.provider != "mock":
            raise ValueError("Only mock provider is supported in Phase 3 scaffolding.")
        if not args.mock_path:
            raise ValueError("--mock-path is required for mock provider.")

        mapping = json.loads(Path(args.mock_path).read_text(encoding="utf-8"))
        provider = MockProvider(mapping)

        mvir = formalize_text_to_mvir(
            text,
            provider,
            problem_id=problem_id,
            strict=args.strict,
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
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
