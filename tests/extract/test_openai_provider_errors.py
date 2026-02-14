"""Offline tests for OpenAI provider error classification."""

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


@pytest.fixture(autouse=True)
def _clear_openai_schema_support_cache() -> None:
    mod.OpenAIProvider._supports_json_schema.clear()


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
    assert "Invalid schema for response_format" in excinfo.value.message
    assert "required/properties rules" in excinfo.value.message


def test_openai_text_format_schema_param_maps_to_bad_schema(
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
                    "message": "json_schema is not supported for this model",
                    "param": "text.format.schema",
                }
            },
            text="bad request",
        )

    monkeypatch.setattr(mod, "_requests_post", _fake_post)
    with pytest.raises(ProviderError) as excinfo:
        provider.complete("hello")
    assert excinfo.value.kind == "bad_schema"
    assert "json_schema is not supported for this model" in excinfo.value.message
    assert "tests/extract/test_openai_schema_strict_rules.py" in excinfo.value.message


def test_extract_error_details_reads_message_param_and_code() -> None:
    response = _FakeResponse(
        400,
        {
            "error": {
                "message": "schema fail",
                "param": "text.format.schema",
                "code": "invalid_json_schema",
            }
        },
        text="raw",
    )
    message, param, code = mod._extract_error_details(response)
    assert message == "schema fail"
    assert param == "text.format.schema"
    assert code == "invalid_json_schema"
