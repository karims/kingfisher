"""Tests deterministic AST repair in formalization flow."""

from __future__ import annotations

import json

from mvir.extract.formalize import formalize_text_to_mvir


class _SingleShotProvider:
    name = "openai"

    def __init__(self, payload: dict) -> None:
        self._payload = payload
        self.calls: list[str] = []

    def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> str:
        _ = temperature
        _ = max_tokens
        self.calls.append(prompt)
        if len(self.calls) > 1:
            raise AssertionError("LLM repair retry should not be called for this test")
        return json.dumps(self._payload)


def test_formalize_repairs_partial_ast_without_second_llm_call() -> None:
    payload = {
        "meta": {"version": "0.1", "id": "repair_case", "generator": "mock"},
        "source": {"text": "Let (x > 0)."},
        "entities": [
            {"id": "x", "kind": "variable", "type": "real", "properties": [], "trace": ["s1"]}
        ],
        "assumptions": [
            {
                "expr": {"node": "Gt", "lhs": {"node": "Symbol"}, "rhs": {"node": "Number"}},
                "kind": "given",
                "trace": ["s1"],
            }
        ],
        "goal": {
            "kind": "prove",
            "expr": {"node": "Bool", "value": True},
            "trace": ["s0"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 12, "text": "Let (x > 0)."},
            {"span_id": "s1", "start": 0, "end": 12, "text": "Let (x > 0)."},
        ],
    }
    provider = _SingleShotProvider(payload)

    mvir = formalize_text_to_mvir("Let (x > 0).", provider, problem_id="repair_case")

    assert len(provider.calls) == 1
    expr = mvir.assumptions[0].expr
    assert expr.node == "Gt"
    assert expr.lhs.id == "x"
    assert expr.rhs.value == 0

