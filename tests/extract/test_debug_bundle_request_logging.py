"""Tests debug bundle request/response logging from provider attributes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mvir.extract.formalize import formalize_text_to_mvir
from mvir.extract.provider_base import ProviderError
from mvir.extract.providers import openai_provider as openai_mod


class _FakeProvider:
    name = "fake"
    model = "fake-model"

    def __init__(self) -> None:
        self.last_request_json = {"model": "fake-model", "input": "PROMPT"}
        self.last_response_json = {"id": "resp_123", "output_text": "{}"}

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
        return "{}"


def test_debug_bundle_writes_request_and_response_json(tmp_path: Path) -> None:
    provider = _FakeProvider()
    debug_dir = tmp_path / "debug"

    with pytest.raises(ValueError):
        formalize_text_to_mvir(
            "x",
            provider,
            problem_id="debug_req_case",
            strict=True,
            debug_dir=str(debug_dir),
        )

    bundle = debug_dir / "debug_req_case"
    request_path = bundle / "request.json"
    response_path = bundle / "response.json"
    assert request_path.exists()
    assert response_path.exists()

    request_payload = json.loads(request_path.read_text(encoding="utf-8"))
    response_payload = json.loads(response_path.read_text(encoding="utf-8"))
    assert request_payload["model"] == "fake-model"
    assert response_payload["id"] == "resp_123"


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self) -> dict:
        return self._payload


def test_debug_bundle_openai_request_logs_json_schema_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = openai_mod.OpenAIProvider(api_key="test-key", model="test-model")
    debug_dir = tmp_path / "debug"

    def _fake_post(url: str, *, headers: dict, json: dict, timeout: float) -> _FakeResponse:
        _ = url
        _ = headers
        _ = timeout
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

    monkeypatch.setattr(openai_mod, "_requests_post", _fake_post)

    with pytest.raises(ProviderError):
        formalize_text_to_mvir(
            "x",
            provider,
            problem_id="debug_openai_schema_case",
            strict=True,
            debug_dir=str(debug_dir),
        )

    request_path = debug_dir / "debug_openai_schema_case" / "request.json"
    assert request_path.exists()
    request_payload = json.loads(request_path.read_text(encoding="utf-8"))
    assert request_payload["text"]["format"]["type"] == "json_schema"
