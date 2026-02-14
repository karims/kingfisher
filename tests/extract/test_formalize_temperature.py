"""Tests for deterministic temperature in formalization calls."""

from __future__ import annotations

import json

from mvir.extract.formalize import formalize_text_to_mvir


class _CaptureProvider:
    name = "capture"

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> str:
        self.calls.append(
            {
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        payload = {
            "meta": {"version": "0.1", "id": "temp_case", "generator": "test"},
            "source": {"text": "x"},
            "entities": [],
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
        return json.dumps(payload)


def test_formalize_text_to_mvir_passes_temperature_zero_by_default() -> None:
    provider = _CaptureProvider()
    mvir = formalize_text_to_mvir("x", provider, problem_id="temp_case")

    assert mvir.meta.id == "temp_case"
    assert len(provider.calls) == 1
    assert provider.calls[0]["temperature"] == 0.0

