"""Explain bundle writer for MVIR outputs."""

from __future__ import annotations

import json
from pathlib import Path

from mvir.core.models import MVIR
from mvir.render.markdown import render_mvir_markdown


def _normalize_trace_text(text: str | None) -> str:
    value = text or ""
    return value.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")


def write_explain_bundle(mvir: MVIR, out_dir: Path) -> None:
    """Write deterministic bundle files for an MVIR document."""

    out_dir.mkdir(parents=True, exist_ok=True)

    payload = mvir.model_dump(by_alias=False, exclude_none=True)
    (out_dir / "mvir.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "mvir.md").write_text(render_mvir_markdown(mvir), encoding="utf-8")

    trace_lines = []
    for span in mvir.trace:
        trace_lines.append(
            f"{span.span_id}\t{span.start}\t{span.end}\t{_normalize_trace_text(span.text)}"
        )
    trace_text = ("\n".join(trace_lines) + "\n") if trace_lines else ""
    (out_dir / "trace.txt").write_text(trace_text, encoding="utf-8")
