"""Tests for MVIR validation repair prompt content."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mvir.core.models import MVIR
from mvir.extract.formalize import _build_validation_repair_prompt


def test_repair_prompt_includes_enum_and_required_field_constraints() -> None:
    with pytest.raises(ValidationError) as excinfo:
        MVIR.model_validate({})

    prompt = _build_validation_repair_prompt(
        problem_id="repair_case",
        validation_error=excinfo.value,
        previous_output='{"meta":{"version":"0.1","id":"repair_case"}}',
    )

    assert 'Assumption.kind MUST be exactly one of: ["given","derived","wlog"]' in prompt
    assert (
        'Goal.kind MUST be exactly one of: ["prove","find","compute","maximize","minimize","exists","counterexample"]'
        in prompt
    )
    assert (
        'Concept.role MUST be exactly one of: ["domain","pattern","candidate_tool","definition","representation_hint"]'
        in prompt
    )
    assert (
        'Entity.kind MUST be exactly one of: ["variable","constant","function","set","sequence","point","vector","object"]'
        in prompt
    )
    assert "Entity requires: id, kind, type" in prompt
    assert "Assumption requires: expr, kind" in prompt
    assert "Goal requires: kind, expr" in prompt
    assert 'If goal.kind is "find", goal.target is required.' in prompt
    assert 'do NOT keep kind="find"' in prompt
    assert '"code": "goal_kind_downgraded"' in prompt
    assert '"details": {"old_kind": "find", "reason": "..."}' in prompt
    assert "Concept requires: id, role" in prompt
    assert "Warning requires: code, message" in prompt
    assert "MVIR.trace must be non-empty" in prompt
    assert "Do NOT change trace spans or span_ids; keep them identical." in prompt
    assert "All trace references must be existing span_ids." in prompt
