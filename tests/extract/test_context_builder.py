"""Tests for extraction prompt context builder."""

from __future__ import annotations

from mvir.extract.context import build_prompt_context


def test_context_builder_s0() -> None:
    text = "Show that x>0."
    context = build_prompt_context({"text": text})

    assert context["s0"]["span_id"] == "s0"
    assert context["s0"]["start"] == 0
    assert context["s0"]["end"] == len(text)
    assert context["s0"]["text"] == text


def test_context_builder_sentence_hints() -> None:
    text = "Let x>0. Find y?"
    context = build_prompt_context({"text": text})

    sentences = context["sentences"]
    assert len(sentences) == 2
    assert sentences[0]["starts_with"] == "let"
    assert sentences[1]["starts_with"] == "find"

    for sentence in sentences:
        assert "starts_with" in sentence
        assert "has_math" in sentence
        assert "has_question_mark" in sentence


def test_context_builder_math_detection() -> None:
    text = r"Compute $x^2+1$. Also x>0."
    context = build_prompt_context({"text": text})

    assert context["sentences"][0]["has_math"] is True
    assert context["sentences"][1]["has_math"] is True
