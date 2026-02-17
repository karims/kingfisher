"""Export deterministic MVIR debug graph JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mvir.analysis.trace_graph import build_trace_graph
from mvir.core.models import load_mvir


def _default_trace_path(mvir_json_path: Path) -> Path:
    return mvir_json_path.with_suffix(".trace.jsonl")


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
    """Run the graph export CLI."""

    parser = argparse.ArgumentParser(description="Export deterministic MVIR debug graph JSON.")
    parser.add_argument("path", help="Path to MVIR JSON file.")
    parser.add_argument("--out", required=True, help="Output graph JSON path.")
    parser.add_argument(
        "--trace",
        help="Optional trace JSONL path. If omitted, tries <mvir_json_path with .trace.jsonl>.",
    )
    args = parser.parse_args(argv)

    try:
        mvir_path = Path(args.path)
        out_path = Path(args.out)
        trace_path = Path(args.trace) if args.trace else _default_trace_path(mvir_path)

        mvir = load_mvir(str(mvir_path))
        trace_events: list[dict] | None = None
        if trace_path.exists():
            trace_events = _load_trace_jsonl(trace_path)

        graph = build_trace_graph(mvir, solver_trace=trace_events)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(graph, ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        print(f"OK: {mvir.meta.id} -> {out_path}")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

