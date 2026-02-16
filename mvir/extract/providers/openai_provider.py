"""OpenAI provider for Phase 4 extraction.

This module keeps all HTTP wiring local to the provider implementation.
"""

from __future__ import annotations

import os
from copy import deepcopy
from typing import Literal

from mvir.extract.openai_json_schema import get_mvir_v01_openai_json_schema
from mvir.extract.provider_base import LLMProvider, ProviderError


class OpenAIProvider(LLMProvider):
    """OpenAI-backed provider for prompt completion."""

    name = "openai"
    _supports_json_schema: dict[str, bool] = {}
    _SCHEMA_HINT = (
        "Your OpenAI strict schema likely violates required/properties rules. "
        "Run: pytest -q tests/extract/test_openai_schema_strict_rules.py"
    )

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_s: float = 30.0,
        format_mode: Literal["json_schema", "json_object"] = "json_schema",
        allow_fallback: bool = False,
        top_p: float | None = None,
        seed: int | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL") or "gpt-4.1-mini"
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com"
        self.timeout_s = timeout_s
        self.format_mode = format_mode
        self.allow_fallback = allow_fallback
        self.top_p = top_p
        self.seed = seed
        self.last_request_json: dict | None = None
        self.last_response_json: dict | None = None

    def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> str:
        """Return a completion for the given prompt."""

        if not self.api_key:
            raise ProviderError(
                provider=self.name,
                kind="auth",
                message="Missing OPENAI_API_KEY.",
                retryable=False,
            )

        normalized_base = self.base_url.rstrip("/")
        if normalized_base.endswith("/v1"):
            url = normalized_base + "/responses"
        else:
            url = normalized_base + "/v1/responses"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": prompt,
            "max_tokens": max_tokens,
            "text": {"format": _build_format_payload(self.format_mode)},
        }
        using_json_schema = self.format_mode == "json_schema"
        if using_json_schema and self._supports_json_schema.get(self.model) is False:
            if self.allow_fallback:
                payload["text"] = {"format": {"type": "json_object"}}
                payload["input"] = _append_json_only_instruction(prompt)
                using_json_schema = False
            else:
                raise ProviderError(
                    provider=self.name,
                    kind="bad_response",
                    message=(
                        f"Model '{self.model}' does not support json_schema enforcement. "
                        "Rerun with --openai-allow-fallback or --openai-format json_object."
                    ),
                    retryable=False,
                )
        if temperature != 0.0:
            payload["temperature"] = temperature
        if self.top_p is not None:
            payload["top_p"] = self.top_p
        if self.seed is not None:
            print("WARNING: seed ignored for OpenAI Responses API")

        retried_temperature = False
        retried_max_tokens = False
        retried_format = False
        response = self._safe_post(url, headers=headers, payload=payload)

        while response.status_code == 400:
            error_message, error_param, error_code = _extract_error_details(response)
            if _is_schema_rejection(
                error_message=error_message,
                error_param=error_param,
                error_code=error_code,
            ):
                self._supports_json_schema[self.model] = False
                original_error = ProviderError(
                    provider=self.name,
                    kind="bad_schema",
                    message=f"{error_message} | {self._SCHEMA_HINT}",
                    retryable=False,
                )
                if self.allow_fallback and not retried_format and using_json_schema:
                    print("OpenAI rejected json_schema; retrying with json_object")
                    payload["text"] = {"format": {"type": "json_object"}}
                    payload["input"] = _append_json_only_instruction(prompt)
                    retried_format = True
                    using_json_schema = False
                    response = self._safe_post(url, headers=headers, payload=payload)
                    if response.status_code == 200:
                        continue
                    raise original_error
                raise original_error
            if (
                error_param == "temperature"
                and "temperature" in payload
                and not retried_temperature
            ):
                payload.pop("temperature", None)
                retried_temperature = True
                response = self._safe_post(url, headers=headers, payload=payload)
                continue
            if (
                error_param in {"max_tokens", "max_output_tokens"}
                and "max_tokens" in payload
                and not retried_max_tokens
            ):
                payload.pop("max_tokens", None)
                retried_max_tokens = True
                response = self._safe_post(url, headers=headers, payload=payload)
                continue
            if (
                self.allow_fallback
                and not retried_format
                and using_json_schema
                and _is_json_schema_unsupported(error_message=error_message, error_param=error_param)
            ):
                self._supports_json_schema[self.model] = False
                payload["text"] = {"format": {"type": "json_object"}}
                payload["input"] = _append_json_only_instruction(prompt)
                retried_format = True
                using_json_schema = False
                response = self._safe_post(url, headers=headers, payload=payload)
                continue
            if (
                not self.allow_fallback
                and using_json_schema
                and _is_json_schema_unsupported(error_message=error_message, error_param=error_param)
            ):
                self._supports_json_schema[self.model] = False
                raise ProviderError(
                    provider=self.name,
                    kind="bad_response",
                    message=(
                        "OpenAI rejected the provided json_schema; see response.json for details. "
                        "Consider using skeleton schema or allow fallback."
                    ),
                    retryable=False,
                )
            break

        if response.status_code != 200:
            error_message, error_param, _ = _extract_error_details(response)
            kind = "bad_response"
            retryable = False
            if response.status_code in (401, 403):
                kind = "auth"
            elif response.status_code == 429:
                kind = "rate_limit"
                retryable = True
            elif response.status_code in (408,):
                kind = "timeout"
                retryable = True
            elif response.status_code >= 500:
                kind = "network"
                retryable = True
            raise ProviderError(
                provider=self.name,
                kind=kind,
                message=_format_http_error_message(
                    response.status_code,
                    error_message,
                    error_param,
                ),
                retryable=retryable,
            )
        if using_json_schema:
            self._supports_json_schema[self.model] = True

        try:
            json_obj = response.json()
        except Exception as exc:
            raise ProviderError(
                provider=self.name,
                kind="bad_response",
                message=f"Malformed JSON response: {exc}",
                retryable=False,
            ) from exc

        text = _extract_text_from_openai_response(json_obj)
        if not text:
            raise ProviderError(
                provider=self.name,
                kind="bad_response",
                message="No text content found in OpenAI response.",
                retryable=False,
            )
        return text

    def _safe_post(self, url: str, *, headers: dict, payload: dict):
        self.last_request_json = deepcopy(payload)
        self.last_response_json = None
        try:
            response = _requests_post(url, headers=headers, json=payload, timeout=self.timeout_s)
        except Exception as exc:  # requests may be unavailable
            if exc.__class__.__name__ == "Timeout":
                raise ProviderError(
                    provider=self.name,
                    kind="timeout",
                    message=str(exc),
                    retryable=True,
                ) from exc
            if exc.__class__.__name__ == "RequestException":
                raise ProviderError(
                    provider=self.name,
                    kind="network",
                    message=str(exc),
                    retryable=True,
                ) from exc
            if exc.__class__.__module__.startswith("requests"):
                raise ProviderError(
                    provider=self.name,
                    kind="network",
                    message=str(exc),
                    retryable=True,
                ) from exc
            raise
        try:
            parsed = response.json()
            if isinstance(parsed, dict):
                self.last_response_json = parsed
            else:
                self.last_response_json = {"_raw": parsed}
        except Exception:
            self.last_response_json = None
        return response


def _requests_post(url: str, *, headers: dict, json: dict, timeout: float):
    """POST helper to isolate requests dependency for easier offline mocking."""

    try:
        import requests
    except Exception as exc:
        raise ProviderError(
            provider="openai",
            kind="network",
            message=f"requests dependency unavailable: {exc}",
            retryable=False,
        ) from exc
    return requests.post(url, headers=headers, json=json, timeout=timeout)


def _extract_text_from_openai_response(json_obj) -> str:
    """Extract assistant text from common OpenAI response shapes."""

    if not isinstance(json_obj, dict):
        return ""

    output_text = json_obj.get("output_text")
    if isinstance(output_text, str) and output_text:
        return output_text

    choices = json_obj.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str) and content:
                return content
            if isinstance(content, list):
                chunks: list[str] = []
                for item in content:
                    if isinstance(item, dict):
                        text = item.get("text")
                        if isinstance(text, str):
                            chunks.append(text)
                if chunks:
                    return "".join(chunks)
        text = first.get("text")
        if isinstance(text, str) and text:
            return text

    output = json_obj.get("output")
    if isinstance(output, list):
        chunks: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if isinstance(part, dict):
                    text = part.get("text")
                    if isinstance(text, str):
                        chunks.append(text)
        if chunks:
            return "".join(chunks)

    return ""


def _extract_error_details(response) -> tuple[str, str | None, str | None]:
    """Extract short error message and param from error response body."""

    try:
        payload = response.json()
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    err = payload.get("error")
    if isinstance(err, dict):
        message = err.get("message")
        param = err.get("param")
        code = err.get("code")
        return (
            message if isinstance(message, str) and message else response.text,
            param if isinstance(param, str) and param else None,
            code if isinstance(code, str) and code else None,
        )
    return (response.text, None, None)


def _format_http_error_message(
    status_code: int,
    error_message: str,
    error_param: str | None,
) -> str:
    parts = [f"HTTP {status_code}"]
    if error_message:
        parts.append(error_message)
    if error_param:
        parts.append(f"param={error_param}")
    return ": ".join(parts[:2]) + (f" ({parts[2]})" if len(parts) > 2 else "")


def _is_json_schema_unsupported(*, error_message: str, error_param: str | None) -> bool:
    msg = error_message.lower()
    if "invalid schema for response_format" in msg or "invalid_json_schema" in msg:
        return False
    references_schema_feature = (
        "json_schema" in msg
        or "response_format" in msg
        or (error_param in {"response_format", "response_format.type", "text.format", "text.format.type"})
    )
    indicates_unsupported = (
        "not supported" in msg
        or "unsupported" in msg
        or "does not support" in msg
    )
    return references_schema_feature and indicates_unsupported


def _is_schema_rejection(
    *,
    error_message: str,
    error_param: str | None,
    error_code: str | None,
) -> bool:
    if error_code == "invalid_json_schema":
        return True
    if error_param == "text.format.schema":
        return True
    return "Invalid schema for response_format" in error_message


def _append_json_only_instruction(prompt: str) -> str:
    instruction = "Output MUST be valid JSON only."
    if instruction in prompt:
        return prompt
    return prompt + "\n\n" + instruction


def _build_format_payload(format_mode: Literal["json_schema", "json_object"]) -> dict:
    if format_mode == "json_object":
        return {"type": "json_object"}
    return {
        "type": "json_schema",
        "name": "mvir_v01",
        "schema": get_mvir_v01_openai_json_schema(),
        "strict": True,
    }
