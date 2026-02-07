"""Tests for grounding contract validation."""

from __future__ import annotations

from mvir.core.models import MVIR
from mvir.extract.contract import validate_grounding_contract


def _base_payload() -> dict:
    text = "x"
    return {
        "meta": {"version": "0.1", "id": "test", "generator": "mock"},
        "source": {"text": text},
        "entities": [{"id": "x", "kind": "variable", "type": "Real", "trace": ["s1"]}],
        "assumptions": [],
        "goal": {
            "kind": "prove",
            "expr": {"node": "Bool", "value": True},
            "trace": ["s1"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 1, "text": text},
            {"span_id": "s1", "start": 0, "end": 1, "text": text},
        ],
    }


def test_contract_missing_s0() -> None:
    payload = _base_payload()
    payload["trace"] = [{"span_id": "s1", "start": 0, "end": 1, "text": "x"}]
    mvir = MVIR.model_validate(payload)

    errors = validate_grounding_contract(mvir)
    assert any("s0" in error for error in errors)


def test_contract_bad_s0_coverage() -> None:
    payload = _base_payload()
    payload["trace"][0]["end"] = 0
    mvir = MVIR.model_validate(payload)

    errors = validate_grounding_contract(mvir)
    assert any("s0 span must cover" in error for error in errors)


def test_contract_substring_mismatch() -> None:
    payload = _base_payload()
    payload["trace"][1]["text"] = "y"
    mvir = MVIR.model_validate(payload)

    errors = validate_grounding_contract(mvir)
    assert any("text mismatch" in error for error in errors)


def test_contract_unknown_span_reference() -> None:
    payload = _base_payload()
    mvir = MVIR.model_validate(payload)
    mvir.entities[0].trace = ["s9"]

    errors = validate_grounding_contract(mvir)
    assert any("Unknown trace ids" in error for error in errors)


def test_contract_valid_mvir_passes() -> None:
    payload = _base_payload()
    mvir = MVIR.model_validate(payload)

    errors = validate_grounding_contract(mvir)
    assert errors == []
