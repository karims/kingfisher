"""Render an MVIR JSON file into a deterministic Markdown report."""

from __future__ import annotations

import argparse
from pathlib import Path

from mvir.core.models import load_mvir
from mvir.render.markdown import render_mvir_markdown


def _default_out_path(input_path: str) -> Path:
    return Path(input_path + ".md")


def main(argv: list[str] | None = None) -> int:
    """Run the MVIR Markdown render CLI."""

    parser = argparse.ArgumentParser(description="Render MVIR JSON into Markdown.")
    parser.add_argument("path", help="Path to MVIR JSON file.")
    parser.add_argument(
        "--out",
        help="Output Markdown path (default: <input>.md).",
    )
    args = parser.parse_args(argv)

    try:
        input_path = Path(args.path)
        out_path = Path(args.out) if args.out else _default_out_path(args.path)

        mvir = load_mvir(str(input_path))
        markdown = render_mvir_markdown(mvir)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8")

        print(f"OK: {mvir.meta.id} -> {out_path}")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
