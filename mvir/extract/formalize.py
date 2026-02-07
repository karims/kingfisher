"""Formalization entrypoints for Phase 3 extraction.

Preprocess is lossless + offsets only; no semantic classification.
Phase 3 uses an LLM to produce MVIR semantics.
Providers must not modify MVIR schema.
"""

from __future__ import annotations

import json

from pydantic import ValidationError

from mvir.core.models import MVIR
from mvir.extract.context import build_prompt_context
from mvir.extract.prompts import build_mvir_prompt
from mvir.extract.provider_base import LLMProvider, Provider, ProviderResult
from mvir.preprocess.context import build_preprocess_output


def formalize(prompt_context: dict, provider: Provider) -> ProviderResult:
    """Formalize prompt context into MVIR using a provider."""

    raise NotImplementedError("Formalization not implemented.")


def formalize_text_to_mvir(
    text: str,
    provider: LLMProvider,
    *,
    problem_id: str = "unknown",
    temperature: float = 0.0,
    max_tokens: int = 2000,
) -> MVIR:
    """Run preprocess + prompt + provider completion and return MVIR."""

    preprocess_result = build_preprocess_output(text).to_dict()
    prompt_context = build_prompt_context(preprocess_result)
    prompt = build_mvir_prompt(prompt_context, problem_id=problem_id)
    response = provider.complete(
        prompt, temperature=temperature, max_tokens=max_tokens
    )

    if "```" in response:
        raise ValueError("Response contains markdown fences; JSON only is required.")

    try:
        payload = json.loads(response)
    except json.JSONDecodeError as exc:
        head = response[:200]
        tail = response[-200:] if len(response) > 200 else response
        raise ValueError(
            f"JSON parse failed: {exc}. head={head!r} tail={tail!r}"
        ) from exc

    try:
        return MVIR.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"MVIR validation failed: {exc}") from exc
