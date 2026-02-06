"""Schema export utilities for MVIR."""

from __future__ import annotations

from pydantic import BaseModel


def export_schema(model: type[BaseModel]) -> dict:
    """Return JSON schema for a Pydantic model."""

    return model.model_json_schema()
