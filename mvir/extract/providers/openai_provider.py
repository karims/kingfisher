"""OpenAI provider for Phase 4 extraction.

This module keeps all HTTP wiring local to the provider implementation.
"""

from __future__ import annotations

import os

from mvir.extract.mvir_json_schema import get_mvir_v01_json_schema
from mvir.extract.provider_base import LLMProvider, ProviderError


class OpenAIProvider(LLMProvider):
    """OpenAI-backed provider for prompt completion."""

    name = "openai"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_s: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL") or "gpt-4.1-mini"
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com"
        self.timeout_s = timeout_s

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
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "mvir_v01",
                    "description": "Kingfisher MVIR v0.1",
                    "schema": get_mvir_v01_json_schema(),
                    "strict": True,
                },
            },
        }
        if temperature != 0.0:
            payload["temperature"] = temperature

        retried_temperature = False
        retried_max_tokens = False
        retried_format = False
        response = self._safe_post(url, headers=headers, payload=payload)

        while response.status_code == 400:
            error_message, error_param = _extract_error_details(response)
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
                not retried_format
                and _is_json_schema_unsupported(error_message=error_message, error_param=error_param)
            ):
                payload["response_format"] = {"type": "json_object"}
                payload["input"] = _append_json_only_instruction(prompt)
                retried_format = True
                response = self._safe_post(url, headers=headers, payload=payload)
                continue
            break

        if response.status_code != 200:
            error_message, error_param = _extract_error_details(response)
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
        try:
            return _requests_post(url, headers=headers, json=payload, timeout=self.timeout_s)
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


def _extract_error_details(response) -> tuple[str, str | None]:
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
        return (
            message if isinstance(message, str) and message else response.text,
            param if isinstance(param, str) and param else None,
        )
    return (response.text, None)


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
    if error_param in {"response_format", "response_format.type"}:
        return "json_schema" in error_message.lower()
    msg = error_message.lower()
    return "json_schema" in msg and ("unsupported" in msg or "not supported" in msg)


def _append_json_only_instruction(prompt: str) -> str:
    instruction = "Output MUST be valid JSON only."
    if instruction in prompt:
        return prompt
    return prompt + "\n\n" + instruction
