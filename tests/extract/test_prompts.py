"""Tests for MVIR prompt construction."""

from __future__ import annotations

import json

from mvir.extract.prompts import build_mvir_prompt


def test_build_mvir_prompt_instructions_and_context() -> None:
    prompt_context = {"text": "Show that x>0.", "s0": {"span_id": "s0"}}
    prompt = build_mvir_prompt(prompt_context, problem_id="abc123")

    assert "Output MUST be valid JSON only (no markdown, no prose)." in prompt
    assert "DO NOT invent meaning." in prompt
    assert "PROBLEM_ID=abc123" in prompt
    assert json.dumps(prompt_context, ensure_ascii=False) in prompt
    assert "```" not in prompt
