"""Tests for strict vs lenient grounding behavior in formalize pipeline."""

from __future__ import annotations

import json

import pytest

from mvir.extract.formalize import formalize_text_to_mvir
from mvir.extract.providers.mock import MockProvider


def _schema_valid_but_grounding_invalid_payload() -> dict:
    return {
        "meta": {"version": "0.1", "id": "strictness_case", "generator": "mock"},
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
            {"span_id": "s1", "start": 0, "end": 1, "text": "y"},
        ],
    }


def test_formalize_strict_raises_on_grounding_failure() -> None:
    payload = json.dumps(_schema_valid_but_grounding_invalid_payload())
    provider = MockProvider({"strictness_case": payload})

    with pytest.raises(ValueError) as excinfo:
        formalize_text_to_mvir("x", provider, problem_id="strictness_case", strict=True)

    assert "Grounding contract failed" in str(excinfo.value)


def test_formalize_lenient_allows_grounding_failure() -> None:
    payload = json.dumps(_schema_valid_but_grounding_invalid_payload())
    provider = MockProvider({"strictness_case": payload})

    mvir = formalize_text_to_mvir("x", provider, problem_id="strictness_case", strict=False)
    assert mvir.meta.id == "strictness_case"

