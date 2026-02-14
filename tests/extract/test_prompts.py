"""Tests for MVIR prompt construction."""

from __future__ import annotations

import json

from mvir.extract.prompts import build_mvir_prompt


def test_build_mvir_prompt_instructions_and_context() -> None:
    prompt_context = {"text": "Show that x>0.", "s0": {"span_id": "s0"}}
    prompt = build_mvir_prompt(prompt_context, problem_id="abc123")

    assert "Output MUST be valid JSON only (no markdown, no prose)." in prompt
    assert "DO NOT invent meaning." in prompt
    assert "entities.kind MUST be one of" in prompt
    assert "trace must be arrays of span_id strings" in prompt
    assert "DO NOT output {op,left,right}" in prompt
    assert '"node":"Gt"' in prompt
    assert 'Symbol MUST include "id".' in prompt
    assert 'Number MUST include "value".' in prompt
    assert 'Pow MUST include "base" and "exp".' in prompt
    assert 'Comparators (Eq/Neq/Lt/Le/Gt/Ge/Divides) MUST include "lhs" and "rhs".' in prompt
    assert 'Never output placeholder nodes like {"node":"Symbol"} or {"node":"Number"}.' in prompt
    assert 'x^2 >= 0 => {"node":"Ge"' in prompt
    assert "Do NOT change trace spans or span_ids." in prompt
    assert "goal is ONE object" in prompt
    assert "PROBLEM_ID=abc123" in prompt
    assert json.dumps(prompt_context, ensure_ascii=False) in prompt
    assert "```" not in prompt
