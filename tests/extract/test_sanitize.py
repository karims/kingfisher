"""Tests for deterministic MVIR payload sanitization."""

from __future__ import annotations

from mvir.core.models import MVIR
from mvir.extract.sanitize import sanitize_mvir_payload


def test_sanitize_payload_fixes_common_near_valid_shapes() -> None:
    payload = {
        "meta": {"version": "0.1", "id": "sanitize_case"},
        "source": {"text": "Let x > 0."},
        "entities": [
            {
                "id": "x",
                "kind": "variable",
                "trace": ["s1"],
            }
        ],
        "assumptions": [
            {
                "expr": {
                    "node": "Gt",
                    "lhs": {"node": "Symbol", "id": "x"},
                    "rhs": {"node": "Number", "value": 0},
                },
                "kind": "assumption",
                "trace": ["s1"],
            }
        ],
        "goal": [
            {
                "kind": "goal",
                "expr": {
                    "node": "Gt",
                    "lhs": {"node": "Symbol", "id": "x"},
                    "rhs": {"node": "Number", "value": 0},
                },
                "trace": ["s1"],
            },
            {
                "kind": "compute",
                "expr": {"node": "Number", "value": 1},
                "trace": ["s1"],
            },
        ],
        "concepts": [
            {"id": "c1", "role": "theorem", "trace": ["s1"]},
            {"id": "c2", "role": "formula", "trace": ["s1"]},
        ],
        "warnings": [{"message": "check this", "trace": ["s1"]}],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 10, "text": "Let x > 0."},
            {"span_id": "s1", "start": 0, "end": 10, "text": "Let x > 0."},
        ],
    }

    sanitized = sanitize_mvir_payload(payload)
    mvir = MVIR.model_validate(sanitized)

    assert mvir.entities[0].type == "Unknown"
    assert mvir.entities[0].properties == []
    assert mvir.assumptions[0].kind.value == "given"
    assert mvir.goal.kind.value == "prove"
    assert mvir.concepts[0].role.value == "definition"
    assert mvir.concepts[1].role.value == "definition"
    assert any(w.code == "multiple_goals" for w in mvir.warnings)
    assert any(w.code == "unspecified" for w in mvir.warnings)
    assert mvir.meta.generator is None
    assert mvir.source.normalized_text is None

