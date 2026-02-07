"""Mock provider for Phase 3 extraction.

Preprocess is lossless + offsets only; no semantic classification.
Phase 3 uses an LLM to produce MVIR semantics.
Providers must not modify MVIR schema.
"""

from __future__ import annotations

from mvir.core.models import MVIR
from mvir.extract.provider_base import ProviderResult


def extract(prompt_context: dict) -> ProviderResult:
    """Placeholder extraction implementation."""

    raise NotImplementedError("Mock provider not implemented.")
