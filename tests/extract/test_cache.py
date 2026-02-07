"""Tests for file-based response cache."""

from __future__ import annotations

from mvir.extract.cache import ResponseCache


def test_cache_key_determinism(tmp_path) -> None:
    cache = ResponseCache(tmp_path)
    key1 = cache.make_key(
        provider_name="openai",
        model_name="gpt-4.1-mini",
        temperature=0.0,
        max_tokens=2000,
        prompt="hello",
    )
    key2 = cache.make_key(
        provider_name="openai",
        model_name="gpt-4.1-mini",
        temperature=0.0,
        max_tokens=2000,
        prompt="hello",
    )
    assert key1 == key2


def test_cache_set_get_roundtrip(tmp_path) -> None:
    cache = ResponseCache(tmp_path)
    key = cache.make_key(
        provider_name="ollama",
        model_name="llama3",
        temperature=0.2,
        max_tokens=512,
        prompt="prompt text",
    )
    cache.set(key, "raw provider output")
    assert cache.get(key) == "raw provider output"


def test_cache_miss_returns_none(tmp_path) -> None:
    cache = ResponseCache(tmp_path)
    assert cache.get("missing-key") is None

