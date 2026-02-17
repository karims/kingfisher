"""Render an MVIR JSON file into a Markdown report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mvir.core.models import MVIR
from mvir.render.markdown import render_mvir_markdown


def _candidate_trace_paths(mvir_json_path: Path) -> list[Path]:
    return [
        Path(str(mvir_json_path) + ".trace.jsonl"),
        mvir_json_path.with_suffix(".trace.jsonl"),
    ]


def _load_trace_jsonl(path: Path) -> list[dict]:
    events: list[dict] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except Exception:
            print(f"WARNING: ignored invalid trace line {idx} in {path}")
            continue
        if isinstance(payload, dict):
            events.append(payload)
        else:
            print(f"WARNING: ignored non-object trace line {idx} in {path}")
    return events


def main(argv: list[str] | None = None) -> int:
    """Run the report CLI."""

    parser = argparse.ArgumentParser(description="Render MVIR JSON into Markdown report.")
    parser.add_argument("path", help="Path to MVIR JSON file.")
    parser.add_argument("--out", required=True, help="Output Markdown path.")
    parser.add_argument(
        "--trace",
        help="Optional trace JSONL path. If omitted, auto-discovers nearby trace files.",
    )
    args = parser.parse_args(argv)

    try:
        mvir_path = Path(args.path)
        out_path = Path(args.out)
        if not mvir_path.exists():
            raise FileNotFoundError(f"MVIR file not found: {mvir_path}")

        try:
            payload = json.loads(mvir_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in MVIR file: {mvir_path} ({exc})") from exc
        mvir = MVIR.model_validate(payload)

        trace_events: list[dict] | None = None
        trace_paths = [Path(args.trace)] if args.trace else _candidate_trace_paths(mvir_path)
        for candidate in trace_paths:
            if candidate.exists():
                trace_events = _load_trace_jsonl(candidate)
                break

        markdown = render_mvir_markdown(mvir, solver_trace=trace_events)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8")

        print(f"OK: {mvir.meta.id} -> {out_path}")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

