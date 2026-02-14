"""Tests for json_schema fallback behavior and capability caching."""

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


def test_openai_invalid_schema_falls_back_to_json_object_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = mod.OpenAIProvider(
        api_key="test-key",
        model="test-model",
        format_mode="json_schema",
        allow_fallback=True,
    )
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
                        "message": "Invalid schema for response_format 'mvir_v01': oneOf is not permitted",
                        "param": "text.format.schema",
                        "code": "invalid_json_schema",
                    }
                },
                text="bad request",
            )
        return _FakeResponse(200, {"output_text": '{"ok":true}'})

    monkeypatch.setattr(mod, "_requests_post", _fake_post)
    out = provider.complete("hello")
    assert out == '{"ok":true}'
    assert len(calls) == 2
    assert calls[0]["text"]["format"]["type"] == "json_schema"
    assert calls[1]["text"]["format"]["type"] == "json_object"
    assert mod.OpenAIProvider._supports_json_schema.get("test-model") is False


def test_openai_invalid_schema_raises_when_fallback_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = mod.OpenAIProvider(
        api_key="test-key",
        model="test-model",
        format_mode="json_schema",
        allow_fallback=False,
    )

    def _fake_post(url: str, *, headers: dict, json: dict, timeout: float) -> _FakeResponse:
        _ = url
        _ = headers
        _ = json
        _ = timeout
        return _FakeResponse(
            400,
            {
                "error": {
                    "message": "Invalid schema for response_format 'mvir_v01': oneOf is not permitted",
                    "param": "text.format.schema",
                    "code": "invalid_json_schema",
                }
            },
            text="bad request",
        )

    monkeypatch.setattr(mod, "_requests_post", _fake_post)
    with pytest.raises(ProviderError) as excinfo:
        provider.complete("hello")
    assert excinfo.value.kind == "bad_schema"
    assert mod.OpenAIProvider._supports_json_schema.get("test-model") is False

