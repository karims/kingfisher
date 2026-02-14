"""Tests debug bundle request/response logging from provider attributes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mvir.extract.formalize import formalize_text_to_mvir


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

