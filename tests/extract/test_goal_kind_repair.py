"""Tests for goal kind repair when find target is missing."""

from __future__ import annotations

import json

from mvir.extract.formalize import formalize_text_to_mvir
from mvir.extract.providers.mock import MockProvider


def test_formalize_repairs_find_without_target_by_downgrading_kind() -> None:
    payload = {
        "meta": {"version": "0.1", "id": "goal_repair_case", "generator": "mock"},
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
    provider = MockProvider({"goal_repair_case": json.dumps(payload)})

    mvir = formalize_text_to_mvir("Find x.", provider, problem_id="goal_repair_case")

    assert mvir.goal.kind.value != "find"
    warning = next((w for w in mvir.warnings if w.code == "goal_kind_downgraded"), None)
    assert warning is not None
    assert warning.details is not None
    assert warning.details.get("old_kind") == "find"
