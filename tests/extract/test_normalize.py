"""Tests for deterministic normalization of near-MVIR payloads."""

from __future__ import annotations

from copy import deepcopy

from mvir.core.models import MVIR
from mvir.extract.normalize import normalize_llm_payload


def _raw_like_llm_payload() -> dict:
    return {
        "meta": {"version": "0.1", "id": "norm_case", "generator": "mock"},
        "source": {"text": "x > 0"},
        "entities": [{"id": "x", "kind": "variable", "type": "Real", "trace": ["s1"]}],
        "assumptions": [
            {
                "expr": {
                    "op": ">",
                    "left": {"node": "var", "name": "x"},
                    "right": {"node": "const", "value": 0},
                },
                "trace": ["s1"],
            }
        ],
        "goal": [
            {
                "kind": "find",
                "expr": {
                    "op": "=",
                    "left": {"node": "var", "name": "x"},
                    "right": {"node": "const", "value": 1},
                },
                "trace": ["s1"],
            },
            {
                "role": "prove",
                "expr": {
                    "op": ">=",
                    "left": {
                        "op": "+",
                        "left": {
                            "op": "^",
                            "left": {"node": "var", "name": "x"},
                            "right": {"node": "const", "value": 2},
                        },
                        "right": {"node": "const", "value": 1},
                    },
                    "right": {"node": "const", "value": 0},
                },
                "trace": ["s1"],
            },
        ],
        "concepts": [{"id": "c1", "trace": ["s1"]}],
        "warnings": [{"message": "missing code", "trace": ["s1"]}],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 5, "text": "x > 0"},
            {"span_id": "s1", "start": 0, "end": 5, "text": "x > 0"},
        ],
    }


def test_normalize_llm_payload_schema_valid_and_deterministic() -> None:
    raw = _raw_like_llm_payload()
    normalized_once = normalize_llm_payload(raw)
    normalized_twice = normalize_llm_payload(deepcopy(normalized_once))

    assert normalized_once == normalized_twice

    assumption = normalized_once["assumptions"][0]
    assert assumption["kind"] == "given"
    assert assumption["expr"]["node"] == "Gt"
    assert assumption["expr"]["lhs"]["node"] == "Symbol"
    assert assumption["expr"]["rhs"]["node"] == "Number"

    assert isinstance(normalized_once["goal"], dict)
    assert normalized_once["goal"]["kind"] == "prove"
    assert normalized_once["concepts"][0]["role"] == "definition"
    assert normalized_once["warnings"][0]["code"] == "unspecified"
    assert any(w.get("code") == "dropped_goals" for w in normalized_once["warnings"])

    mvir = MVIR.model_validate(normalized_once)
    assert mvir.meta.id == "norm_case"

