"""Offline tests for OpenAI unsupported-parameter retry behavior."""

from __future__ import annotations

import pytest

from mvir.extract.provider_base import ProviderError
from mvir.extract.providers import openai_provider as mod


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self) -> dict:
        return self._payload


def test_openai_retries_without_temperature_on_unsupported_param(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = mod.OpenAIProvider(api_key="test-key", model="test-model")
    calls: list[dict] = []

    def _fake_post(url: str, *, headers: dict, json: dict, timeout: float) -> _FakeResponse:
        _ = url
        _ = headers
        _ = timeout
        calls.append(dict(json))
        if len(calls) == 1:
            return _FakeResponse(
                400,
                {
                    "error": {
                        "message": "Unsupported parameter: 'temperature' is not supported with this model.",
                        "param": "temperature",
                    }
                },
                text="bad request",
            )
        return _FakeResponse(
            200,
            {
                "output": [
                    {
                        "content": [
                            {"type": "output_text", "text": "recovered"},
                        ]
                    }
                ]
            },
        )

    monkeypatch.setattr(mod, "_requests_post", _fake_post)
    out = provider.complete("hello", temperature=0.7, max_tokens=100)
    assert out == "recovered"
    assert len(calls) == 2
    assert "temperature" in calls[0]
    assert "temperature" not in calls[1]


def test_openai_retry_failure_raises_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = mod.OpenAIProvider(api_key="test-key", model="test-model")
    calls: list[dict] = []

    def _fake_post(url: str, *, headers: dict, json: dict, timeout: float) -> _FakeResponse:
        _ = url
        _ = headers
        _ = timeout
        calls.append(dict(json))
        return _FakeResponse(
            400,
            {
                "error": {
                    "message": "Unsupported parameter: 'temperature' is not supported with this model.",
                    "param": "temperature",
                }
            },
            text="bad request",
        )

    monkeypatch.setattr(mod, "_requests_post", _fake_post)

    with pytest.raises(ProviderError) as excinfo:
        provider.complete("hello", temperature=0.7, max_tokens=100)

    err = excinfo.value
    assert err.kind == "bad_response"
    message = str(err)
    assert "HTTP 400" in message
    assert "Unsupported parameter" in message
    assert "temperature" in message
    assert len(calls) == 2

