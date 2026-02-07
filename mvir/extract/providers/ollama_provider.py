"""Ollama provider for Phase 4 extraction."""

from __future__ import annotations

import os

from mvir.extract.provider_base import LLMProvider, ProviderError


class OllamaProvider(LLMProvider):
    """Ollama-backed provider for prompt completion."""

    name = "ollama"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str | None = None,
        endpoint: str | None = None,
        timeout_s: float = 30.0,
    ) -> None:
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
        self.model = model or os.getenv("OLLAMA_MODEL") or "llama3"
        self.endpoint = endpoint or os.getenv("OLLAMA_ENDPOINT") or "/api/generate"
        self.timeout_s = timeout_s

    def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> str:
        """Return a completion for the given prompt."""

        url = self.base_url.rstrip("/") + "/" + self.endpoint.lstrip("/")
        payload = {
            "model": self.model,
            "stream": False,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        # If endpoint is chat-like, send chat-style messages instead of prompt.
        if "chat" in self.endpoint:
            payload.pop("prompt", None)
            payload["messages"] = [{"role": "user", "content": prompt}]

        try:
            response = _requests_post(url, json=payload, timeout=self.timeout_s)
        except Exception as exc:
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
            if response.status_code == 429:
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

        text = _extract_text_from_ollama_response(json_obj)
        if not text:
            raise ProviderError(
                provider=self.name,
                kind="bad_response",
                message="No text content found in Ollama response.",
                retryable=False,
            )
        return text


def _requests_post(url: str, *, json: dict, timeout: float):
    """POST helper to isolate requests dependency for easier offline mocking."""

    try:
        import requests
    except Exception as exc:
        raise ProviderError(
            provider="ollama",
            kind="network",
            message=f"requests dependency unavailable: {exc}",
            retryable=False,
        ) from exc
    return requests.post(url, json=json, timeout=timeout)


def _extract_text_from_ollama_response(json_obj) -> str:
    """Extract text from common Ollama response shapes."""

    if not isinstance(json_obj, dict):
        return ""
    response = json_obj.get("response")
    if isinstance(response, str) and response:
        return response
    message = json_obj.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content:
            return content
    return ""
