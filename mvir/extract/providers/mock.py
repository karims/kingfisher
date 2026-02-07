"""Mock provider for Phase 3 extraction.

Preprocess is lossless + offsets only; no semantic classification.
Phase 3 uses an LLM to produce MVIR semantics.
Providers must not modify MVIR schema.
"""

from __future__ import annotations

from dataclasses import dataclass

from mvir.extract.provider_base import LLMProvider, ProviderError


@dataclass(frozen=True)
class MockProvider(LLMProvider):
    """Mock provider that maps PROBLEM_ID to canned responses."""

    mapping: dict[str, str]
    name: str = "mock"

    def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> str:
        """Return a canned response for a known PROBLEM_ID."""

        _ = temperature
        _ = max_tokens
        problem_id = None
        for line in prompt.splitlines():
            if line.startswith("PROBLEM_ID="):
                problem_id = line.split("=", 1)[1].strip()
                break
        if not problem_id:
            raise ProviderError(
                provider=self.name,
                kind="bad_response",
                message="Missing PROBLEM_ID in prompt.",
                retryable=False,
            )
        if problem_id not in self.mapping:
            keys = ", ".join(sorted(self.mapping.keys()))
            raise ProviderError(
                provider=self.name,
                kind="bad_response",
                message=f"Unknown PROBLEM_ID '{problem_id}'. Available keys: {keys}",
                retryable=False,
            )
        return self.mapping[problem_id]
