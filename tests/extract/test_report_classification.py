"""Tests for exception classification in extraction reports."""

from __future__ import annotations

from pydantic import ValidationError

from mvir.core.models import MVIR
from mvir.extract.provider_base import ProviderError
from mvir.extract.report import FailureKind, classify_exception


def test_classify_provider_error() -> None:
    exc = ProviderError(
        provider="mock",
        kind="bad_response",
        message="bad payload",
        retryable=False,
    )
    kind, message = classify_exception(exc)
    assert kind == FailureKind.PROVIDER
    assert "bad payload" in message


def test_classify_json_parse_marker() -> None:
    exc = ValueError("JSON parse failed: bad json")
    kind, _ = classify_exception(exc)
    assert kind == FailureKind.JSON_PARSE


def test_classify_schema_validation_error() -> None:
    try:
        MVIR.model_validate({})
    except ValidationError as exc:
        kind, _ = classify_exception(exc)
        assert kind == FailureKind.SCHEMA_VALIDATION
    else:
        raise AssertionError("Expected ValidationError")


def test_classify_grounding_contract_marker() -> None:
    exc = ValueError("Grounding contract failed: bad spans")
    kind, _ = classify_exception(exc)
    assert kind == FailureKind.GROUNDING_CONTRACT


def test_classify_unknown_and_truncate_message() -> None:
    exc = RuntimeError("x" * 500)
    kind, message = classify_exception(exc)
    assert kind == FailureKind.UNKNOWN
    assert len(message) <= 243
    assert message.endswith("...")

