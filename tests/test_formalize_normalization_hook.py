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
    assert any(w.code == "invalid_assumption_expr_dropped" for w in mvir.warnings)


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
    warning = next((w for w in mvir.warnings if w.code == "invalid_assumption_expr_dropped"), None)
    assert warning is not None
    assert warning.details is not None
    assert warning.details.get("reason") == "incomplete_expr"
    assert isinstance(warning.details.get("raw_expr"), dict)


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


def test_formalize_normalization_hook_sanitizes_nested_invalid_mul_in_assumption_expr() -> None:
    payload = {
        "meta": {"version": "0.1", "id": "norm_hook_nested_mul", "generator": "test"},
        "source": {"text": "Assume (1 + 2) = 3."},
        "entities": [],
        "assumptions": [
            {
                "expr": {
                    "node": "Eq",
                    "lhs": {
                        "node": "Add",
                        "args": [
                            {"node": "Number", "value": 1},
                            {"node": "Mul"},
                            {"node": "Number", "value": 2},
                        ],
                    },
                    "rhs": {"node": "Number", "value": 3},
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
            {"span_id": "s0", "start": 0, "end": 19, "text": "Assume (1 + 2) = 3."},
            {"span_id": "s1", "start": 0, "end": 19, "text": "Assume (1 + 2) = 3."},
        ],
    }

    normalized = _normalize_payload_expr_fields(payload)
    mvir = MVIR.model_validate(normalized)

    assert len(mvir.assumptions) == 1
    lhs = mvir.assumptions[0].expr.lhs
    assert lhs.node == "Add"
    assert len(lhs.args) == 2


def test_formalize_normalization_hook_drops_assumption_when_nested_add_args_all_invalid() -> None:
    payload = {
        "meta": {"version": "0.1", "id": "norm_hook_nested_mul_all_bad", "generator": "test"},
        "source": {"text": "Assume bad sum."},
        "entities": [],
        "assumptions": [
            {
                "expr": {
                    "node": "Eq",
                    "lhs": {"node": "Add", "args": [{"node": "Mul"}]},
                    "rhs": {"node": "Number", "value": 3},
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
            {"span_id": "s0", "start": 0, "end": 14, "text": "Assume bad sum."},
            {"span_id": "s1", "start": 0, "end": 14, "text": "Assume bad sum."},
        ],
    }

    normalized = _normalize_payload_expr_fields(payload)
    mvir = MVIR.model_validate(normalized)

    assert mvir.assumptions == []
    assert any(w.code == "invalid_assumption_expr_dropped" for w in mvir.warnings)


def test_formalize_normalization_hook_replaces_invalid_goal_expr_when_degrade_enabled() -> None:
    payload = {
        "meta": {"version": "0.1", "id": "norm_hook_bad_goal_expr", "generator": "test"},
        "source": {"text": "Compute something."},
        "entities": [],
        "assumptions": [],
        "goal": {
            "kind": "compute",
            "expr": {"node": "Add"},
            "trace": ["s1"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 18, "text": "Compute something."},
            {"span_id": "s1", "start": 0, "end": 18, "text": "Compute something."},
        ],
    }

    normalized = _normalize_payload_expr_fields(payload, degrade_on_invalid_goal_expr=True)
    mvir = MVIR.model_validate(normalized)

    assert mvir.goal.kind.value == "prove"
    assert mvir.goal.expr.node == "Bool"
    warning = next((w for w in mvir.warnings if w.code == "invalid_goal_expr_replaced"), None)
    assert warning is not None
    assert warning.details is not None
    assert warning.details.get("reason") == "goal_expr_not_parseable"
