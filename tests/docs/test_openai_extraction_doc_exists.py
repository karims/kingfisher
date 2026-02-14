"""Docs existence test for OpenAI extraction guide."""

from __future__ import annotations

from pathlib import Path


def test_openai_extraction_doc_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "docs" / "OPENAI_EXTRACTION.md").exists()

