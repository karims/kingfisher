"""Formalization entrypoints for Phase 3 extraction.

Preprocess is lossless + offsets only; no semantic classification.
Phase 3 uses an LLM to produce MVIR semantics.
Providers must not modify MVIR schema.
"""

from __future__ import annotations

import json
import traceback
from pathlib import Path

from pydantic import ValidationError

from mvir.core.models import MVIR
from mvir.extract.cache import ResponseCache
from mvir.extract.context import build_prompt_context
from mvir.extract.contract import validate_grounding_contract
from mvir.extract.prompts import build_mvir_prompt
from mvir.extract.provider_base import LLMProvider, Provider, ProviderResult
from mvir.extract.report import classify_exception
from mvir.preprocess.context import build_preprocess_output


def formalize(prompt_context: dict, provider: Provider) -> ProviderResult:
    """Formalize prompt context into MVIR using a provider."""

    raise NotImplementedError("Formalization not implemented.")


def try_repair_json_output(raw: str) -> str | None:
    """Try deterministic minimal repair of nearly-JSON LLM output."""

    repaired = raw.strip()

    if "```" in repaired:
        first = repaired.find("```")
        second = repaired.find("```", first + 3)
        if first != -1 and second != -1 and second > first:
            repaired = repaired[first + 3 : second].strip()

    first_brace = repaired.find("{")
    if first_brace != -1 and first_brace > 0:
        repaired = repaired[first_brace:]

    last_brace = repaired.rfind("}")
    if last_brace != -1 and last_brace < len(repaired) - 1:
        repaired = repaired[: last_brace + 1]

    if repaired.startswith("{") and repaired.endswith("}"):
        return repaired
    return None


def formalize_text_to_mvir(
    text: str,
    provider: LLMProvider,
    *,
    problem_id: str = "unknown",
    temperature: float = 0.0,
    max_tokens: int = 2000,
    cache: ResponseCache | None = None,
    use_cache: bool = True,
    strict: bool = True,
    repair: bool = True,
    debug_dir: str | None = None,
) -> MVIR:
    """Run preprocess + prompt + provider completion and return MVIR."""

    preprocess_result = build_preprocess_output(text).to_dict()
    prompt_context = build_prompt_context(preprocess_result)
    prompt = build_mvir_prompt(prompt_context, problem_id=problem_id)
    provider_name = getattr(provider, "name", provider.__class__.__name__)
    model_name = getattr(provider, "model", None)

    response: str | None = None
    try:
        cache_key: str | None = None
        if cache is not None:
            cache_key = cache.make_key(
                provider_name=str(provider_name),
                model_name=str(model_name) if model_name is not None else None,
                temperature=temperature,
                max_tokens=max_tokens,
                prompt=prompt,
            )
            if use_cache:
                response = cache.get(cache_key)

        if response is None:
            response = provider.complete(
                prompt, temperature=temperature, max_tokens=max_tokens
            )
            if cache is not None and cache_key is not None:
                cache.set(cache_key, response)

        try:
            payload = json.loads(response)
        except json.JSONDecodeError as exc:
            payload = None
            if repair:
                repaired = try_repair_json_output(response)
                if repaired is not None:
                    try:
                        payload = json.loads(repaired)
                    except json.JSONDecodeError:
                        payload = None
            if payload is None:
                head = response[:200]
                tail = response[-200:] if len(response) > 200 else response
                raise ValueError(
                    f"JSON parse failed: {exc}. head={head!r} tail={tail!r}"
                ) from exc

        try:
            mvir = MVIR.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"MVIR validation failed: {exc}") from exc

        errors = validate_grounding_contract(mvir)
        if strict and errors:
            raise ValueError("Grounding contract failed: " + "; ".join(errors))

        return mvir
    except Exception as exc:
        _write_debug_bundle(
            debug_dir=debug_dir,
            problem_id=problem_id,
            source_text=text,
            preprocess_result=preprocess_result,
            prompt=prompt,
            raw_output=response,
            exc=exc,
        )
        raise


def _write_debug_bundle(
    *,
    debug_dir: str | None,
    problem_id: str,
    source_text: str,
    preprocess_result: dict,
    prompt: str,
    raw_output: str | None,
    exc: Exception,
) -> None:
    """Best-effort debug bundle writer; never raises."""

    if not debug_dir:
        return
    try:
        base = Path(debug_dir) / problem_id
        base.mkdir(parents=True, exist_ok=True)
        (base / "source.txt").write_text(source_text, encoding="utf-8")
        (base / "preprocess.json").write_text(
            json.dumps(preprocess_result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (base / "prompt.txt").write_text(prompt, encoding="utf-8")
        if raw_output is not None:
            (base / "raw_output.txt").write_text(raw_output, encoding="utf-8")
        kind, message = classify_exception(exc)
        error_text = "\n".join(
            [
                f"kind: {kind.value}",
                f"message: {message}",
                f"exception: {exc!r}",
                "",
                "traceback:",
                traceback.format_exc(),
            ]
        )
        (base / "error.txt").write_text(error_text, encoding="utf-8")
    except Exception:
        return
