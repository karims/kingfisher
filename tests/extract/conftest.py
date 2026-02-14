"""Shared fixtures for extract tests."""

from __future__ import annotations

import pytest

from mvir.extract.providers import openai_provider as openai_mod


@pytest.fixture(autouse=True)
def _reset_openai_json_schema_support_cache() -> None:
    openai_mod.OpenAIProvider._supports_json_schema.clear()

