"""Provider base classes for Phase 3 extraction.

Preprocess is lossless + offsets only; no semantic classification.
Phase 3 uses an LLM to produce MVIR semantics.
Providers must not modify MVIR schema.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from mvir.core.models import MVIR


@dataclass(frozen=True)
class ProviderResult:
    """Result container for MVIR extraction."""

    mvir: MVIR
    raw_response: str | None = None


class Provider(Protocol):
    """Provider protocol for MVIR extraction."""

    def extract(self, prompt_context: dict) -> ProviderResult:
        """Extract MVIR using a provider implementation."""

        raise NotImplementedError
