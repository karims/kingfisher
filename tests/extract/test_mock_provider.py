"""Tests for the mock LLM provider."""

from __future__ import annotations

import pytest

from mvir.extract.provider_base import ProviderError
from mvir.extract.providers.mock import MockProvider


def test_mock_provider_returns_mapping() -> None:
    provider = MockProvider({"abc": "OK"})
    prompt = "PROBLEM_ID=abc\nINPUT=..."

    assert provider.complete(prompt) == "OK"


def test_mock_provider_missing_key() -> None:
    provider = MockProvider({"abc": "OK"})
    prompt = "PROBLEM_ID=missing\nINPUT=..."

    with pytest.raises(ProviderError) as excinfo:
        provider.complete(prompt)

    message = str(excinfo.value)
    assert "missing" in message
    assert "abc" in message


def test_mock_provider_extracts_problem_id() -> None:
    provider = MockProvider({"id_1": "payload"})
    prompt = "\n".join(
        [
            "HEADER",
            "PROBLEM_ID=id_1",
            "FOOTER",
        ]
    )

    assert provider.complete(prompt) == "payload"
