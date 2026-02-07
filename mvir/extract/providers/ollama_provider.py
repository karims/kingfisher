"""Ollama provider scaffolding for Phase 4 extraction.

Network-backed providers are optional in tests and local workflows.
This module intentionally exposes placeholder APIs only.
"""

from __future__ import annotations

from dataclasses import dataclass

from mvir.extract.provider_base import LLMProvider, ProviderError


@dataclass(frozen=True)
class OllamaProvider(LLMProvider):
    """Placeholder Ollama LLM provider.

    Concrete request/response wiring is intentionally deferred.
    """

    model: str
    host: str | None = None
    name: str = "ollama"

    def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> str:
        """Return a completion for the given prompt."""

        _ = prompt
        _ = temperature
        _ = max_tokens
        raise ProviderError(
            provider=self.name,
            kind="bad_response",
            message="Ollama provider wiring is not implemented in Phase 4 scaffolding.",
            retryable=False,
        )
