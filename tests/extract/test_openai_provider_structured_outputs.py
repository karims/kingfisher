"""Offline tests for OpenAI Structured Outputs payload behavior."""

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


def test_openai_uses_json_schema_response_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = mod.OpenAIProvider(api_key="test-key", model="test-model")
    seen_payloads: list[dict] = []

    def _fake_post(url: str, *, headers: dict, json: dict, timeout: float) -> _FakeResponse:
        _ = url
        _ = headers
        _ = timeout
        seen_payloads.append(dict(json))
        return _FakeResponse(200, {"output_text": "ok-json"})

    monkeypatch.setattr(mod, "_requests_post", _fake_post)
    out = provider.complete("hello")
    assert out == "ok-json"

    assert len(seen_payloads) == 1
    assert "response_format" not in seen_payloads[0]
    fmt = seen_payloads[0]["text"]["format"]
    assert fmt["type"] == "json_schema"
    assert fmt["name"] == "mvir_v01"
    assert fmt["strict"] is True
    assert "schema" in fmt


def test_openai_falls_back_to_json_object_when_json_schema_unsupported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = mod.OpenAIProvider(
        api_key="test-key",
        model="test-model",
        allow_fallback=True,
    )
    seen_payloads: list[dict] = []

    def _fake_post(url: str, *, headers: dict, json: dict, timeout: float) -> _FakeResponse:
        _ = url
        _ = headers
        _ = timeout
        seen_payloads.append(dict(json))
        if len(seen_payloads) == 1:
            return _FakeResponse(
                400,
                {
                    "error": {
                        "message": "text.format json_schema is not supported for this model",
                        "param": "text.format",
                    }
                },
                text="bad request",
            )
        return _FakeResponse(200, {"output_text": "fallback-ok"})

    monkeypatch.setattr(mod, "_requests_post", _fake_post)
    out = provider.complete("hello")
    assert out == "fallback-ok"

    assert len(seen_payloads) == 2
    assert "response_format" not in seen_payloads[0]
    assert "response_format" not in seen_payloads[1]
    assert seen_payloads[0]["text"]["format"]["type"] == "json_schema"
    assert seen_payloads[1]["text"]["format"]["type"] == "json_object"
    assert "JSON only" in seen_payloads[1]["input"]


def test_openai_schema_invalid_raises_bad_schema_without_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = mod.OpenAIProvider(
        api_key="test-key",
        model="test-model",
        allow_fallback=True,
    )
    seen_payloads: list[dict] = []

    def _fake_post(url: str, *, headers: dict, json: dict, timeout: float) -> _FakeResponse:
        _ = url
        _ = headers
        _ = timeout
        seen_payloads.append(dict(json))
        if len(seen_payloads) == 1:
            return _FakeResponse(
                400,
                {
                    "error": {
                        "message": "Invalid schema for response_format 'mvir_v01': additionalProperties is required to be supplied and to be false.",
                        "param": "text.format.schema",
                    }
                },
                text="bad request",
            )
        return _FakeResponse(200, {"output_text": "schema-fallback-ok"})

    monkeypatch.setattr(mod, "_requests_post", _fake_post)
    with pytest.raises(ProviderError) as excinfo:
        provider.complete("hello")
    err = excinfo.value
    assert err.kind == "bad_schema"
    assert len(seen_payloads) == 1
    assert seen_payloads[0]["text"]["format"]["type"] == "json_schema"


def test_openai_no_fallback_by_default_raises_on_unsupported_json_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = mod.OpenAIProvider(api_key="test-key", model="test-model")
    seen_payloads: list[dict] = []

    def _fake_post(url: str, *, headers: dict, json: dict, timeout: float) -> _FakeResponse:
        _ = url
        _ = headers
        _ = timeout
        seen_payloads.append(dict(json))
        return _FakeResponse(
            400,
            {
                "error": {
                    "message": "text.format json_schema is not supported for this model",
                    "param": "text.format",
                }
            },
            text="bad request",
        )

    monkeypatch.setattr(mod, "_requests_post", _fake_post)
    with pytest.raises(ProviderError) as excinfo:
        provider.complete("hello")
    assert "OpenAI rejected the provided json_schema" in str(excinfo.value)
    assert len(seen_payloads) == 1
