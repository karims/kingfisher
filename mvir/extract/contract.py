"""Extraction contract definitions for Phase 3.

Preprocess is lossless + offsets only; no semantic classification.
Phase 3 uses an LLM to produce MVIR semantics.
Providers must not modify MVIR schema.
"""

from __future__ import annotations


def validate_contract(payload: dict) -> None:
    """Validate provider output against extraction contract."""

    raise NotImplementedError("Contract validation not implemented.")
