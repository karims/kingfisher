"""Tests for post-LLM math surface enrichment."""

from __future__ import annotations

import json
from pathlib import Path

from mvir.cli import formalize as cli_formalize
from mvir.extract.context import build_prompt_context
from mvir.preprocess.context import build_preprocess_output


def test_formalize_with_mock_enriches_source_math_surface(tmp_path: Path) -> None:
    problem_path = Path("examples/problems/latex_smoke_01.txt")
    text = problem_path.read_text(encoding="utf-8")

    pre = build_preprocess_output(text)
    context = build_prompt_context(pre.to_dict())

    trace = [{"span_id": "s0", "start": 0, "end": len(text), "text": text}]
    trace.extend(context["sentences"])
    goal_trace_id = context["sentences"][0]["span_id"] if context["sentences"] else "s0"

    payload = {
        "meta": {"version": "0.1", "id": "latex_smoke_01", "generator": "mock"},
        "source": {"text": text},
        "entities": [],
        "assumptions": [],
        "goal": {
            "kind": "prove",
            "expr": {"node": "Bool", "value": True},
            "trace": [goal_trace_id],
        },
        "concepts": [],
        "warnings": [],
        "trace": trace,
    }
    mock_path = tmp_path / "mock_responses.json"
    out_path = tmp_path / "latex_smoke_01.math_surface.test.json"
    mock_path.write_text(json.dumps({"latex_smoke_01": json.dumps(payload)}), encoding="utf-8")

    rc = cli_formalize.main(
        [str(problem_path), "--provider", "mock", "--mock-path", str(mock_path), "--out", str(out_path)]
    )
    assert rc == 0
    dumped = json.loads(out_path.read_text(encoding="utf-8"))

    source = dumped.get("source", {})
    math_surface = source.get("math_surface")
    assert isinstance(math_surface, list)
    assert math_surface
    assert any(
        isinstance(item, dict)
        and isinstance(item.get("raw_latex"), str)
        and ("\\sum" in item["raw_latex"] or "\\frac" in item["raw_latex"])
        for item in math_surface
    )
