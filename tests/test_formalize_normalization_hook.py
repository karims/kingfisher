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


def test_formalize_normalization_hook_drops_invalid_assumption_to_warning() -> None:
    payload = {
        "meta": {"version": "0.1", "id": "norm_hook_bad_assumption", "generator": "test"},
        "source": {"text": "Show x > 0."},
        "entities": [],
        "assumptions": [
            {
                "expr": {"node": "Eq", "lhs": {"node": "Symbol", "id": "x"}},
                "kind": "given",
                "trace": ["s1"],
            }
        ],
        "goal": {
            "kind": "prove",
            "expr": {"node": "Bool", "value": True},
            "trace": ["s0"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 10, "text": "Show x > 0."},
            {"span_id": "s1", "start": 0, "end": 10, "text": "Show x > 0."},
        ],
    }

    normalized = _normalize_payload_expr_fields(payload)
    mvir = MVIR.model_validate(normalized)

    assert mvir.assumptions == []
    assert any(w.code == "dropped_assumption" for w in mvir.warnings)


def test_formalize_normalization_hook_drops_incomplete_sum_assumption_without_null_stuffing() -> None:
    payload = {
        "meta": {"version": "0.1", "id": "norm_hook_bad_sum_assumption", "generator": "test"},
        "source": {"text": "Also sum from k=1 to n of k equals something."},
        "entities": [
            {"id": "k", "kind": "variable", "type": "integer", "properties": [], "trace": ["s1"]},
            {"id": "n", "kind": "variable", "type": "integer", "properties": [], "trace": ["s1"]},
        ],
        "assumptions": [
            {
                "expr": {
                    "node": "Eq",
                    "lhs": {
                        "node": "Sum",
                        "var": "k",
                        "from": {"node": "Number", "value": 1},
                    },
                    "rhs": {"node": "Symbol", "id": "n"},
                },
                "kind": "given",
                "trace": ["s1"],
            }
        ],
        "goal": {
            "kind": "prove",
            "expr": {"node": "Bool", "value": True},
            "trace": ["s0"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 44, "text": "Also sum from k=1 to n of k equals something."},
            {"span_id": "s1", "start": 0, "end": 44, "text": "Also sum from k=1 to n of k equals something."},
        ],
    }

    normalized = _normalize_payload_expr_fields(payload)
    mvir = MVIR.model_validate(normalized)

    assert mvir.assumptions == []
    warning = next((w for w in mvir.warnings if w.code == "dropped_assumption"), None)
    assert warning is not None
    assert warning.details is not None
    assert warning.details.get("reason") == "incomplete_expr"


def test_formalize_normalization_hook_downgrades_find_without_target() -> None:
    payload = {
        "meta": {"version": "0.1", "id": "norm_hook_find_missing_target", "generator": "test"},
        "source": {"text": "Find x."},
        "entities": [{"id": "x", "kind": "variable", "type": "integer", "properties": [], "trace": ["s1"]}],
        "assumptions": [],
        "goal": {
            "kind": "find",
            "expr": {"node": "Bool", "value": True},
            "target": None,
            "trace": ["s1"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 7, "text": "Find x."},
            {"span_id": "s1", "start": 0, "end": 7, "text": "Find x."},
        ],
    }

    normalized = _normalize_payload_expr_fields(payload)
    mvir = MVIR.model_validate(normalized)

    assert mvir.goal.kind.value != "find"
    warning = next((w for w in mvir.warnings if w.code == "goal_kind_downgraded"), None)
    assert warning is not None
    assert warning.details is not None
    assert warning.details.get("old_kind") == "find"
