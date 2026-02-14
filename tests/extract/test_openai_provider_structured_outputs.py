"""Offline tests for OpenAI Structured Outputs payload behavior."""

from __future__ import annotations

import pytest

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
    response_format = seen_payloads[0]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["name"] == "mvir_v01"
    assert response_format["json_schema"]["strict"] is True
    assert "schema" in response_format["json_schema"]


def test_openai_falls_back_to_json_object_when_json_schema_unsupported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = mod.OpenAIProvider(api_key="test-key", model="test-model")
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
                        "message": "response_format json_schema is not supported for this model",
                        "param": "response_format",
                    }
                },
                text="bad request",
            )
        return _FakeResponse(200, {"output_text": "fallback-ok"})

    monkeypatch.setattr(mod, "_requests_post", _fake_post)
    out = provider.complete("hello")
    assert out == "fallback-ok"

    assert len(seen_payloads) == 2
    assert seen_payloads[0]["response_format"]["type"] == "json_schema"
    assert seen_payloads[1]["response_format"]["type"] == "json_object"
    assert "JSON only" in seen_payloads[1]["input"]

