"""OpenAI provider scaffolding for Phase 4 extraction.

Network-backed providers are optional in tests and local workflows.
This module intentionally exposes placeholder APIs only.
"""

from __future__ import annotations

from dataclasses import dataclass

from mvir.extract.provider_base import LLMProvider, ProviderError


@dataclass(frozen=True)
class OpenAIProvider(LLMProvider):
    """Placeholder OpenAI LLM provider.

    Concrete request/response wiring is intentionally deferred.
    """

    model: str
    api_key: str | None = None
    base_url: str | None = None
    name: str = "openai"

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
            message="OpenAI provider wiring is not implemented in Phase 4 scaffolding.",
            retryable=False,
        )
