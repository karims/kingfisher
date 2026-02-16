"""Regression tests for OpenAI request format payloads."""

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


@pytest.fixture(autouse=True)
def _clear_openai_schema_support_cache() -> None:
    mod.OpenAIProvider._supports_json_schema.clear()


def test_openai_request_uses_json_schema_format_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = mod.OpenAIProvider(
        api_key="test-key",
        model="test-model",
        format_mode="json_schema",
        allow_fallback=False,
    )
    captured: list[dict] = []

    def _fake_post(url: str, *, headers: dict, json: dict, timeout: float) -> _FakeResponse:
        _ = url
        _ = headers
        _ = timeout
        captured.append(dict(json))
        return _FakeResponse(200, {"output_text": "{}"})

    monkeypatch.setattr(mod, "_requests_post", _fake_post)
    out = provider.complete(prompt="x")
    assert out == "{}"
    assert len(captured) == 1

    payload = captured[0]
    assert payload["text"]["format"]["type"] == "json_schema"
    assert payload["text"]["format"]["strict"] is True
    assert "schema" in payload["text"]["format"]


def test_openai_request_fallback_switches_to_json_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = mod.OpenAIProvider(
        api_key="test-key",
        model="test-model",
        format_mode="json_schema",
        allow_fallback=True,
    )
    captured: list[dict] = []

    def _fake_post(url: str, *, headers: dict, json: dict, timeout: float) -> _FakeResponse:
        _ = url
        _ = headers
        _ = timeout
        captured.append(dict(json))
        if len(captured) == 1:
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
        return _FakeResponse(200, {"output_text": "{}"})

    monkeypatch.setattr(mod, "_requests_post", _fake_post)
    out = provider.complete(prompt="x")
    assert out == "{}"
    assert len(captured) == 2
    assert captured[0]["text"]["format"]["type"] == "json_schema"
    assert captured[1]["text"]["format"]["type"] == "json_object"


def test_openai_request_does_not_send_seed_param(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    provider = mod.OpenAIProvider(
        api_key="test-key",
        model="test-model",
        format_mode="json_object",
        seed=123,
        top_p=1.0,
    )
    captured: list[dict] = []

    def _fake_post(url: str, *, headers: dict, json: dict, timeout: float) -> _FakeResponse:
        _ = url
        _ = headers
        _ = timeout
        captured.append(dict(json))
        return _FakeResponse(200, {"output_text": "{}"})

    monkeypatch.setattr(mod, "_requests_post", _fake_post)
    out = provider.complete(prompt="x")
    stdout = capsys.readouterr().out

    assert out == "{}"
    assert len(captured) == 1
    assert "seed" not in captured[0]
    assert captured[0]["top_p"] == 1.0
    assert "seed ignored for OpenAI Responses API" in stdout
