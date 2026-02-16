"""Tests for goal-level MVIR validation constraints."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mvir.core.models import MVIR


def test_mvir_find_goal_requires_target() -> None:
    payload = {
        "meta": {"version": "0.1", "id": "find_missing_target", "generator": "test"},
        "source": {"text": "Find x."},
        "entities": [{"id": "x", "kind": "variable", "type": "integer", "properties": [], "trace": ["s1"]}],
        "assumptions": [],
        "goal": {"kind": "find", "expr": {"node": "Bool", "value": True}, "trace": ["s1"]},
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 7, "text": "Find x."},
            {"span_id": "s1", "start": 0, "end": 7, "text": "Find x."},
        ],
    }

    with pytest.raises(ValidationError) as excinfo:
        MVIR.model_validate(payload)
    assert "Find goal requires a target." in str(excinfo.value)
