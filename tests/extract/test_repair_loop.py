"""Tests for one-shot MVIR validation repair loop."""

from __future__ import annotations

import json

from mvir.extract.formalize import formalize_text_to_mvir


class _QueuedOpenAIProvider:
    name = "openai"
    model = "test-model"

    def __init__(self, outputs: list[str]) -> None:
        self._outputs = list(outputs)
        self.prompts: list[str] = []

    def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> str:
        _ = temperature
        _ = max_tokens
        self.prompts.append(prompt)
        if not self._outputs:
            raise RuntimeError("No queued provider output")
        return self._outputs.pop(0)


def _invalid_first_payload() -> dict:
    return {
        "meta": {"version": "0.1", "id": "repair_case", "generator": "openai"},
        "source": {"text": "x"},
        "entities": [
            {"id": "x", "kind": "variable", "properties": [], "trace": ["s1"]}
        ],
        "assumptions": [],
        "goal": {
            "kind": "prove",
            "expr": {"node": "Bool", "value": True},
            "trace": ["s0"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 1, "text": "x"},
            {"span_id": "s1", "start": 0, "end": 1, "text": "x"},
        ],
    }


def _fixed_payload() -> dict:
    return {
        "meta": {"version": "0.1", "id": "repair_case", "generator": "openai"},
        "source": {"text": "x"},
        "entities": [
            {
                "id": "x",
                "kind": "variable",
                "type": "real",
                "properties": [],
                "trace": ["s1"],
            }
        ],
        "assumptions": [],
        "goal": {
            "kind": "prove",
            "expr": {"node": "Bool", "value": True},
            "trace": ["s0"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 1, "text": "x"},
            {"span_id": "s1", "start": 0, "end": 1, "text": "x"},
        ],
    }


def test_validation_error_triggers_one_shot_openai_repair() -> None:
    provider = _QueuedOpenAIProvider(
        [json.dumps(_invalid_first_payload()), json.dumps(_fixed_payload())]
    )

    mvir = formalize_text_to_mvir("x", provider, problem_id="repair_case")

    assert mvir.meta.id == "repair_case"
    assert len(provider.prompts) == 2
    assert "You output JSON but it failed MVIR validation." in provider.prompts[1]
    assert "Return corrected JSON only." in provider.prompts[1]
    assert "```" not in provider.prompts[1]

