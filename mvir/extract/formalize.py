"""Formalization entrypoints for Phase 3 extraction.

Preprocess is lossless + offsets only; no semantic classification.
Phase 3 uses an LLM to produce MVIR semantics.
Providers must not modify MVIR schema.
"""

from __future__ import annotations

from mvir.extract.provider_base import Provider, ProviderResult


def formalize(prompt_context: dict, provider: Provider) -> ProviderResult:
    """Formalize prompt context into MVIR using a provider."""

    raise NotImplementedError("Formalization not implemented.")
