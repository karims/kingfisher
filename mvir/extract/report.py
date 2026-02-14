"""Failure classification and run reporting utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum

from pydantic import ValidationError

from mvir.extract.provider_base import ProviderError


class FailureKind(str, Enum):
    """Standardized failure kinds for extraction runs."""

    JSON_PARSE = "json_parse"
    SCHEMA_VALIDATION = "schema_validation"
    GROUNDING_CONTRACT = "grounding_contract"
    PROVIDER = "provider"
    UNKNOWN = "unknown"


_MAX_MESSAGE_LEN = 240


def _truncate_message(message: str, limit: int = _MAX_MESSAGE_LEN) -> str:
    if len(message) <= limit:
        return message
    return message[:limit] + "..."


def classify_exception(exc: Exception) -> tuple[FailureKind, str]:
    """Classify an exception into a failure kind and normalized message."""

    message = str(exc)

    if isinstance(exc, ProviderError):
        return FailureKind.PROVIDER, _truncate_message(message)

    if isinstance(exc, json.JSONDecodeError):
        return FailureKind.JSON_PARSE, _truncate_message(message)

    if isinstance(exc, (TimeoutError, ConnectionError)):
        return FailureKind.PROVIDER, _truncate_message(message)

    if exc.__class__.__module__.startswith("requests"):
        return FailureKind.PROVIDER, _truncate_message(message)

    if isinstance(exc, ValidationError):
        return FailureKind.SCHEMA_VALIDATION, _truncate_message(message)

    if isinstance(exc, ValueError):
        if "Provider call failed" in message:
            return FailureKind.PROVIDER, _truncate_message(message)
        if "JSON parse failed" in message:
            return FailureKind.JSON_PARSE, _truncate_message(message)
        if "MVIR validation failed" in message:
            return FailureKind.SCHEMA_VALIDATION, _truncate_message(message)
        if "Grounding contract failed" in message:
            return FailureKind.GROUNDING_CONTRACT, _truncate_message(message)

    return FailureKind.UNKNOWN, _truncate_message(message)


@dataclass
class RunReport:
    """Aggregated run report for batch formalization."""

    ok: list[str] = field(default_factory=list)
    failed: list[dict] = field(default_factory=list)
