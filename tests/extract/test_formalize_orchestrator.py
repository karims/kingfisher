"""Tests for formalize_text_to_mvir."""

from __future__ import annotations

import json

import pytest

from mvir.extract.formalize import formalize_text_to_mvir
from mvir.extract.providers.mock import MockProvider


def _valid_mvir_payload() -> dict:
    return {
        "meta": {"version": "0.1", "id": "test", "generator": "mock"},
        "source": {"text": "x"},
        "entities": [],
        "assumptions": [],
        "goal": {
            "kind": "prove",
            "expr": {"node": "Bool", "value": True},
            "trace": ["s0"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 1, "text": "x"},
            {"span_id": "s1", "start": 0, "end": 1, "text": "x"},
        ],
    }


def test_formalize_valid_response() -> None:
    payload = json.dumps(_valid_mvir_payload())
    provider = MockProvider({"ok": payload})

    mvir = formalize_text_to_mvir("x", provider, problem_id="ok")

    assert mvir.meta.id == "test"


def test_formalize_invalid_json() -> None:
    provider = MockProvider({"bad": "{not-json}"})

    with pytest.raises(ValueError) as excinfo:
        formalize_text_to_mvir("x", provider, problem_id="bad")

    assert "JSON parse failed" in str(excinfo.value)


def test_formalize_invalid_schema() -> None:
    provider = MockProvider({"bad": "{}"})

    with pytest.raises(ValueError) as excinfo:
        formalize_text_to_mvir("x", provider, problem_id="bad")

    assert "MVIR validation failed" in str(excinfo.value)


def test_formalize_degrade_replaces_invalid_goal_expr() -> None:
    payload = {
        "meta": {"version": "0.1", "id": "degrade_goal_case", "generator": "mock"},
        "source": {"text": "Compute x."},
        "entities": [],
        "assumptions": [],
        "goal": {"kind": "compute", "expr": {"node": "Add"}, "trace": ["s1"]},
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 10, "text": "Compute x."},
            {"span_id": "s1", "start": 0, "end": 10, "text": "Compute x."},
        ],
    }
    provider = MockProvider({"degrade_goal_case": json.dumps(payload)})
    mvir = formalize_text_to_mvir(
        "Compute x.",
        provider,
        problem_id="degrade_goal_case",
        degrade_on_validation_failure=True,
    )
    assert mvir.goal.kind.value == "prove"
    assert mvir.goal.expr.node == "Bool"
    assert any(w.code == "invalid_goal_expr_replaced" for w in mvir.warnings)


def test_formalize_degrade_recovers_minimal_valid_mvir_from_invalid_schema() -> None:
    provider = MockProvider({"degrade_bad_schema": "{}"})
    mvir = formalize_text_to_mvir(
        "x",
        provider,
        problem_id="degrade_bad_schema",
        degrade_on_validation_failure=True,
    )
    assert mvir.meta.id == "degrade_bad_schema"
    assert mvir.goal.expr.node == "Bool"
    assert any(w.code == "invalid_mvir_recovered" for w in mvir.warnings)
