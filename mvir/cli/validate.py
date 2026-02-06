"""Validation CLI placeholder."""

from __future__ import annotations

from mvir.core.models import MvirDocument


def validate_payload(payload: dict) -> MvirDocument:
    """Validate payload against MVIR model placeholder."""

    return MvirDocument.model_validate(payload)
