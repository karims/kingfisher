"""Tests for formalize_text_to_mvir cache behavior."""

from __future__ import annotations

import json

from mvir.extract.cache import ResponseCache
from mvir.extract.formalize import formalize_text_to_mvir


def _valid_mvir_payload() -> dict:
    return {
        "meta": {"version": "0.1", "id": "cache_test", "generator": "mock"},
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


class _CountingMockProvider:
    name = "counting-mock"
    model = "counting-model"

    def __init__(self, response: str) -> None:
        self._response = response
        self.calls = 0

    def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> str:
        _ = prompt
        _ = temperature
        _ = max_tokens
        self.calls += 1
        return self._response


def test_formalize_uses_cache_on_second_call(tmp_path) -> None:
    payload = json.dumps(_valid_mvir_payload())
    provider = _CountingMockProvider(payload)
    cache = ResponseCache(tmp_path / ".mvir_cache")

    mvir1 = formalize_text_to_mvir(
        "x",
        provider,
        problem_id="cache_test",
        cache=cache,
        use_cache=True,
    )
    assert provider.calls == 1

    mvir2 = formalize_text_to_mvir(
        "x",
        provider,
        problem_id="cache_test",
        cache=cache,
        use_cache=True,
    )
    assert provider.calls == 1
    assert mvir1.model_dump(by_alias=False, exclude_none=True) == mvir2.model_dump(
        by_alias=False, exclude_none=True
    )

