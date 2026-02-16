"""Snapshot-style checks for repair prompt AST checklist block."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mvir.core.models import MVIR
from mvir.extract.formalize import _build_validation_repair_prompt


_EXPECTED_CHECKLIST_BLOCK = """AST node checklist (required fields):
- Symbol: id
- Number: value
- Add/Mul: args (>=1)
- Div: num, den
- Pow: base, exp
- Eq/Neq/Lt/Le/Gt/Ge/Divides: lhs, rhs
- Sum: var, from, to, body
- Call: fn, args
"""


def test_repair_prompt_contains_ast_checklist_snapshot_block() -> None:
    with pytest.raises(ValidationError) as excinfo:
        MVIR.model_validate({})
    prompt = _build_validation_repair_prompt(
        problem_id="snapshot_case",
        validation_error=excinfo.value,
        previous_output='{"meta":{"version":"0.1","id":"snapshot_case"}}',
    )
    assert _EXPECTED_CHECKLIST_BLOCK in prompt
