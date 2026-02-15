"""Tests repair prompt includes strict enum and AST constraints."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mvir.core.models import MVIR
from mvir.extract.formalize import _build_validation_repair_prompt


def test_repair_prompt_contains_required_constraints() -> None:
    with pytest.raises(ValidationError) as excinfo:
        MVIR.model_validate({})

    prompt = _build_validation_repair_prompt(
        problem_id="pid",
        validation_error=excinfo.value,
        previous_output='{"meta":{"version":"0.1","id":"pid"}}',
    )

    assert 'Assumption.kind in {"given","derived","wlog"}' in prompt
    assert 'Goal.kind in {"prove","find","compute","maximize","minimize","exists","counterexample"}' in prompt
    assert 'Concept.role in {"domain","pattern","candidate_tool","definition","representation_hint"}' in prompt
    assert 'Symbol must be {"node":"Symbol","id":"x"} not name' in prompt
    assert "Gt/Ge/etc must use lhs/rhs (args only allowed in input but output must be lhs/rhs)" in prompt
    assert "Pow must be base/exp" in prompt
    assert "Do not add fields not in the previous JSON unless required by schema." in prompt
    assert "Do not change trace spans; keep trace identical." in prompt

