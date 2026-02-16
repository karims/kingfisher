"""Offline tests for OpenAI provider."""

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


def test_openai_provider_complete_offline_success(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = mod.OpenAIProvider(api_key="test-key", model="test-model")

    def _fake_post(url: str, *, headers: dict, json: dict, timeout: float) -> _FakeResponse:
        assert "/v1/responses" in url
        assert headers["Authorization"] == "Bearer test-key"
        assert json["model"] == "test-model"
        assert json["input"] == "hello"
        assert timeout == (10, provider.timeout_s)
        return _FakeResponse(
            200,
            {
                "output": [
                    {
                        "content": [
                            {"type": "output_text", "text": "mocked response"},
                        ]
                    }
                ]
            },
        )

    monkeypatch.setattr(mod, "_requests_post", _fake_post)
    assert provider.complete("hello") == "mocked response"


def test_openai_provider_missing_api_key_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = mod.OpenAIProvider(api_key=None, model="test-model")

    with pytest.raises(ProviderError) as excinfo:
        provider.complete("hello")

    err = excinfo.value
    assert err.kind == "auth"
    assert err.retryable is False
