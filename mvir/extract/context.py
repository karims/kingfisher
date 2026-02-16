"""Prompt context handling for Phase 3 extraction.

Preprocess is lossless + offsets only; no semantic classification.
Phase 3 uses an LLM to produce MVIR semantics.
Providers must not modify MVIR schema.
"""

from __future__ import annotations

import re

def build_extract_context(preprocess: dict, prompt_context: dict) -> dict:
    """Combine preprocess and prompt context for providers."""

    raise NotImplementedError("Extraction context assembly not implemented.")


_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]?")
_STARTS_WITH = [
    "let",
    "assume",
    "suppose",
    "given",
    "show",
    "prove",
    "compute",
    "find",
    "define",
    "also",
    "consider",
]
_MATH_TOKENS = {"$", "\\", "^", "_", "≥", "≤", "∈", "≠", "=", "<", ">", "+", "-", "*", "/"}
_MATH_REGEX = re.compile(r"[A-Za-z]\s*[<>]=?\s*[A-Za-z0-9]")


def _starts_with_hint(text: str) -> str:
    stripped = text.strip().lower()
    for token in _STARTS_WITH:
        if stripped.startswith(token):
            return token
    return "none"


def _has_math_hint(text: str) -> bool:
    if any(token in text for token in _MATH_TOKENS):
        return True
    return _MATH_REGEX.search(text) is not None


def build_prompt_context(preprocess_result: dict) -> dict:
    """Build extraction prompt context from preprocess outputs."""

    source_text = preprocess_result.get("text", "")
    sentences: list[dict] = []
    provided_spans = preprocess_result.get("spans")
    if isinstance(provided_spans, list):
        for i, span in enumerate(provided_spans, start=1):
            if not isinstance(span, dict):
                continue
            start = span.get("start")
            end = span.get("end")
            snippet = span.get("text")
            if not isinstance(start, int) or not isinstance(end, int) or not isinstance(snippet, str):
                continue
            if not snippet.strip():
                continue
            span_id = span.get("span_id")
            if not isinstance(span_id, str) or not span_id:
                span_id = f"s{i}"
            sentences.append(
                {
                    "span_id": span_id,
                    "start": start,
                    "end": end,
                    "text": snippet,
                    "starts_with": _starts_with_hint(snippet),
                    "has_math": _has_math_hint(snippet),
                    "has_question_mark": "?" in snippet,
                }
            )
    else:
        sentence_id = 1
        for match in _SENTENCE_RE.finditer(source_text):
            start = match.start()
            end = match.end()
            snippet = source_text[start:end]
            if not snippet.strip():
                continue
            sentences.append(
                {
                    "span_id": f"s{sentence_id}",
                    "start": start,
                    "end": end,
                    "text": snippet,
                    "starts_with": _starts_with_hint(snippet),
                    "has_math": _has_math_hint(snippet),
                    "has_question_mark": "?" in snippet,
                }
            )
            sentence_id += 1

    return {
        "source_text": source_text,
        "s0": {
            "span_id": "s0",
            "start": 0,
            "end": len(source_text),
            "text": source_text,
        },
        "sentences": sentences,
    }
