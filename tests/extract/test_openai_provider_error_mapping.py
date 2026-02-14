"""Tests for OpenAI provider error classification paths."""

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


def test_openai_invalid_json_schema_maps_to_bad_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = mod.OpenAIProvider(api_key="test-key", model="test-model")

    def _fake_post(url: str, *, headers: dict, json: dict, timeout: float) -> _FakeResponse:
        _ = url
        _ = headers
        _ = json
        _ = timeout
        return _FakeResponse(
            400,
            {
                "error": {
                    "message": "Invalid schema for response_format 'mvir_v01': 'oneOf' is not permitted.",
                    "param": "text.format.schema",
                    "code": "invalid_json_schema",
                }
            },
            text="bad request",
        )

    monkeypatch.setattr(mod, "_requests_post", _fake_post)

    with pytest.raises(ProviderError) as excinfo:
        provider.complete("x")

    err = excinfo.value
    assert err.kind == "bad_schema"
    assert "oneOf" in str(err)


def test_openai_unsupported_json_schema_maps_to_no_fallback_error(
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
                    "message": "json_schema is not supported for this model",
                    "param": "text.format",
                }
            },
            text="bad request",
        )

    monkeypatch.setattr(mod, "_requests_post", _fake_post)

    with pytest.raises(ProviderError) as excinfo:
        provider.complete("x")

    err = excinfo.value
    assert err.kind == "bad_response"
    assert "OpenAI rejected the provided json_schema" in str(err)

