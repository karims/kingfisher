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
    assert 'Never output placeholder Expr nodes. If node=="Sum", you MUST provide var, from, to, body.' in prompt
    assert "Never include unrelated keys filled with null to satisfy schemas." in prompt
    assert "If an assumption expression cannot be constructed with all required fields of its AST node, DO NOT insert placeholder null fields." in prompt
    assert '"code": "dropped_assumption"' in prompt
    assert '"details": {"reason": "..."}' in prompt
    assert "FORBIDDEN: id:null, value:null, args:null, lhs:null, rhs:null, base:null, exp:null, num:null, den:null, from:null, to:null, body:null." in prompt
    assert "If a secondary task expression cannot be represented correctly with available AST nodes, DO NOT put it in assumptions." in prompt
    assert 'add a warning with code="unparsed_math" and trace=[span_id]' in prompt
    assert "Keep goal as primary; secondary tasks go into warning only." in prompt
    assert "AST examples:" in prompt
    assert 'Sum example: {"node":"Sum","var":"k","from":{"node":"Number","value":1},"to":{"node":"Symbol","id":"n"},"body":{"node":"Symbol","id":"k"}}' in prompt
    assert 'Div example: {"node":"Div","num":{"node":"Symbol","id":"a"},"den":{"node":"Number","value":2}}' in prompt
    assert 'Symbol example: {"node":"Symbol","id":"x"} (never {"node":"Symbol","name":"x"})' in prompt
    assert "Do not add fields not in the previous JSON unless required by schema." in prompt
    assert "Do not change trace spans; keep trace identical." in prompt
