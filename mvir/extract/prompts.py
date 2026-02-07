"""Prompt templates for Phase 3 extraction.

Preprocess is lossless + offsets only; no semantic classification.
Phase 3 uses an LLM to produce MVIR semantics.
Providers must not modify MVIR schema.
"""

from __future__ import annotations


def build_prompt(prompt_context: dict) -> str:
    """Build provider prompt text from context."""

    raise NotImplementedError("Prompt construction not implemented.")
