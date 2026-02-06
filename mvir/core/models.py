"""Pydantic models for MVIR payloads."""

from __future__ import annotations

from pydantic import BaseModel


class MvirDocument(BaseModel):
    """Top-level MVIR document placeholder."""

    version: str
    root: dict
