"""Offline tests for Ollama provider."""

from __future__ import annotations

import pytest

from mvir.extract.provider_base import ProviderError
from mvir.extract.providers import ollama_provider as mod


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self) -> dict:
        return self._payload


def test_ollama_provider_complete_offline_success(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = mod.OllamaProvider(model="test-model", endpoint="/api/generate")

    def _fake_post(url: str, *, json: dict, timeout: float) -> _FakeResponse:
        assert "/api/generate" in url
        assert json["model"] == "test-model"
        assert json["prompt"] == "hello"
        assert timeout == provider.timeout_s
        return _FakeResponse(200, {"response": "mocked ollama response"})

    monkeypatch.setattr(mod, "_requests_post", _fake_post)
    assert provider.complete("hello") == "mocked ollama response"


def test_ollama_provider_error_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = mod.OllamaProvider(model="test-model")

    def _fake_post(url: str, *, json: dict, timeout: float) -> _FakeResponse:
        _ = url
        _ = json
        _ = timeout
        return _FakeResponse(429, {}, text="rate limited")

    monkeypatch.setattr(mod, "_requests_post", _fake_post)

    with pytest.raises(ProviderError) as excinfo:
        provider.complete("hello")

    err = excinfo.value
    assert err.kind == "rate_limit"
    assert err.retryable is True

