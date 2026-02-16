from __future__ import annotations

import json
from pathlib import Path

from mvir.core.models import MVIR
from mvir.render.markdown import render_expr, render_mvir_markdown


_FIXTURE_PATH = Path("out/mvir/latex_smoke_01.json")


def _fallback_payload() -> dict:
    return {
        "meta": {"version": "0.1", "id": "tiny_case", "generator": "test"},
        "source": {"text": "Let x > 0. Show x^2 >= 0."},
        "entities": [
            {"id": "x", "kind": "variable", "type": "real", "properties": [], "trace": ["s1"]}
        ],
        "assumptions": [
            {
                "expr": {
                    "node": "Gt",
                    "lhs": {"node": "Symbol", "id": "x"},
                    "rhs": {"node": "Number", "value": 0},
                },
                "kind": "given",
                "trace": ["s1"],
            }
        ],
        "goal": {
            "kind": "prove",
            "expr": {
                "node": "Ge",
                "lhs": {
                    "node": "Pow",
                    "base": {"node": "Symbol", "id": "x"},
                    "exp": {"node": "Number", "value": 2},
                },
                "rhs": {"node": "Number", "value": 0},
            },
            "trace": ["s2"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 25, "text": "Let x > 0. Show x^2 >= 0."},
            {"span_id": "s1", "start": 0, "end": 9, "text": "Let x > 0."},
            {"span_id": "s2", "start": 10, "end": 25, "text": "Show x^2 >= 0."},
        ],
    }


def _load_case() -> MVIR:
    if _FIXTURE_PATH.exists():
        payload = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    else:
        payload = _fallback_payload()
    return MVIR.model_validate(payload)


def test_render_mvir_markdown_contains_required_sections_and_goal_pow() -> None:
    mvir = _load_case()

    report = render_mvir_markdown(mvir)

    assert f"# MVIR Report: {mvir.meta.id}" in report
    assert "## Meta" in report
    assert "## Source" in report
    assert "## Trace Spans" in report
    assert "## Entities" in report
    assert "## Assumptions" in report
    assert "## Goal" in report
    assert "## Concepts" in report
    assert "## Warnings" in report
    assert "## Solver Trace" in report
    assert "x^2" in report


def test_render_expr_pow_uses_compact_atomic_form() -> None:
    mvir = MVIR.model_validate(_fallback_payload())
    goal_expr = mvir.goal.expr

    rendered = render_expr(goal_expr)

    assert "x^2" in rendered
    assert ">=" in rendered
