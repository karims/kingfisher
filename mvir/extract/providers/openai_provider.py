"""OpenAI provider for Phase 4 extraction.

This module keeps all HTTP wiring local to the provider implementation.
"""

from __future__ import annotations

import os

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
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

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

        if response.status_code != 200:
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
                message=f"HTTP {response.status_code}: {response.text}",
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
