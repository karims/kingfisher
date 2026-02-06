"""Validation CLI for MVIR JSON files."""

from __future__ import annotations

import argparse
import sys

from mvir.core.models import load_mvir


def main(argv: list[str] | None = None) -> int:
    """Run MVIR validation from the command line."""

    parser = argparse.ArgumentParser(description="Validate an MVIR JSON file.")
    parser.add_argument("path", help="Path to MVIR JSON file.")
    args = parser.parse_args(argv)

    try:
        mvir = load_mvir(args.path)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {exc}")
        return 1

    print(f"OK: {mvir.meta.id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
