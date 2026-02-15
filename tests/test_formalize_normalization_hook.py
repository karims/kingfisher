"""Tests for formalize normalization hook over assumption/goal expressions."""

from __future__ import annotations

from mvir.core.models import MVIR
from mvir.extract.formalize import _normalize_payload_expr_fields


def test_formalize_normalization_hook_makes_payload_mvir_valid() -> None:
    payload = {
        "meta": {"version": "0.1", "id": "norm_hook_case", "generator": "test"},
        "source": {"text": "Let x > 0. Show that x^2 >= 0."},
        "entities": [
            {"id": "x", "kind": "variable", "type": "real", "properties": [], "trace": ["s1"]}
        ],
        "assumptions": [
            {
                "expr": {
                    "node": "Gt",
                    "args": [
                        {"node": "Symbol", "name": "x"},
                        {"node": "Number", "value": 0},
                    ],
                },
                "kind": "given",
                "trace": ["s1"],
            }
        ],
        "goal": {
            "kind": "prove",
            "expr": {
                "node": "Pow",
                "args": [
                    {"node": "Symbol", "name": "x"},
                    {"node": "Number", "value": 2},
                ],
            },
            "trace": ["s2"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 30, "text": "Let x > 0. Show that x^2 >= 0."},
            {"span_id": "s1", "start": 0, "end": 9, "text": "Let x > 0."},
            {"span_id": "s2", "start": 10, "end": 30, "text": "Show that x^2 >= 0."},
        ],
    }

    normalized = _normalize_payload_expr_fields(payload)
    mvir = MVIR.model_validate(normalized)

    assert mvir.assumptions[0].expr.node == "Gt"
    assert mvir.assumptions[0].expr.lhs.id == "x"
    assert mvir.goal.expr.node == "Pow"
    assert mvir.goal.expr.base.id == "x"
    assert mvir.goal.expr.exp.value == 2

