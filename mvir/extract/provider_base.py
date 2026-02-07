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


@dataclass(frozen=True)
class ProviderRequest:
    """Typed request payload for provider completion calls."""

    prompt: str
    temperature: float = 0.0
    max_tokens: int = 2000
    timeout_s: float | None = None


class ProviderError(Exception):
    """Standardized provider error with retry metadata."""

    def __init__(
        self,
        *,
        provider: str,
        kind: str,
        message: str,
        retryable: bool,
    ) -> None:
        self.provider = provider
        self.kind = kind
        self.message = message
        self.retryable = retryable
        super().__init__(self.__str__())

    def __str__(self) -> str:
        return (
            f"ProviderError(provider={self.provider!r}, kind={self.kind!r}, "
            f"retryable={self.retryable}): {self.message}"
        )


class Provider(Protocol):
    """Provider protocol for MVIR extraction."""

    def extract(self, prompt_context: dict) -> ProviderResult:
        """Extract MVIR using a provider implementation."""

        raise NotImplementedError


class LLMProvider(Protocol):
    """LLM provider abstraction for prompt completion."""

    name: str

    def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> str:
        """Complete the given prompt and return raw text.

        Implementations should raise ProviderError for provider failures.
        """

        raise NotImplementedError
