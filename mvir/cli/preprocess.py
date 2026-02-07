"""CLI for preprocess reporting."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mvir.preprocess.context import build_preprocess_output, build_prompt_context


def main(argv: list[str] | None = None) -> int:
    """Run preprocess CLI for a text file."""

    parser = argparse.ArgumentParser(description="Generate preprocess report JSON.")
    parser.add_argument("path", help="Path to a plain text input file.")
    parser.add_argument(
        "--context",
        action="store_true",
        help="Print prompt context JSON instead of preprocess output.",
    )
    parser.add_argument(
        "--both",
        action="store_true",
        help="Print both preprocess output and prompt context JSON.",
    )
    args = parser.parse_args(argv)

    if args.context and args.both:
        print("ERROR: --context and --both are mutually exclusive")
        return 1

    try:
        text = Path(args.path).read_text(encoding="utf-8")
        preprocess = build_preprocess_output(text).to_dict()
        if args.context:
            payload = build_prompt_context(preprocess)
        elif args.both:
            payload = {
                "preprocess": preprocess,
                "prompt_context": build_prompt_context(preprocess),
            }
        else:
            payload = preprocess
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {exc}")
        return 1

    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
