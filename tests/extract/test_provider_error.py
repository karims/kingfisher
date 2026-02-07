"""Tests for standardized provider error model."""

from __future__ import annotations

from mvir.extract.provider_base import ProviderError


def test_provider_error_fields_exist() -> None:
    err = ProviderError(
        provider="openai",
        kind="timeout",
        message="Request timed out.",
        retryable=True,
    )

    assert err.provider == "openai"
    assert err.kind == "timeout"
    assert err.message == "Request timed out."
    assert err.retryable is True


def test_provider_error_str_includes_provider_and_kind() -> None:
    err = ProviderError(
        provider="ollama",
        kind="network",
        message="Connection refused.",
        retryable=True,
    )

    text = str(err)
    assert "ollama" in text
    assert "network" in text

