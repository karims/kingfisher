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
        "trace": [{"span_id": "s0", "start": 0, "end": 1, "text": "x"}],
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
