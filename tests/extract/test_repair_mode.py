"""Tests for deterministic JSON repair mode in formalization."""

from __future__ import annotations

import json

import pytest

from mvir.extract.formalize import formalize_text_to_mvir, try_repair_json_output
from mvir.extract.providers.mock import MockProvider


def _valid_mvir_payload() -> dict:
    return {
        "meta": {"version": "0.1", "id": "repair_case", "generator": "mock"},
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


@pytest.mark.parametrize(
    ("raw_builder", "label"),
    [
        (lambda s: f"```json\n{s}\n```", "fenced JSON"),
        (lambda s: f"Here is JSON:\n{s}", "leading prose"),
        (lambda s: f"{s}\nDone.", "trailing prose"),
    ],
)
def test_repair_mode_repairs_and_formalizes(raw_builder, label: str) -> None:
    payload_str = json.dumps(_valid_mvir_payload())
    raw = raw_builder(payload_str)
    repaired = try_repair_json_output(raw)

    assert repaired == payload_str, label

    provider = MockProvider({"repair_case": raw})
    mvir = formalize_text_to_mvir("x", provider, problem_id="repair_case", repair=True)
    assert mvir.meta.id == "repair_case"


def test_repair_mode_non_json_returns_none_and_raises() -> None:
    raw = "totally non-json output"
    assert try_repair_json_output(raw) is None

    provider = MockProvider({"repair_case": raw})
    with pytest.raises(ValueError) as excinfo:
        formalize_text_to_mvir("x", provider, problem_id="repair_case", repair=True)
    assert "JSON parse failed" in str(excinfo.value)

