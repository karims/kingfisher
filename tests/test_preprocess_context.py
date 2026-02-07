"""Tests for preprocess context output."""

from __future__ import annotations

from mvir.preprocess.context import build_preprocess_output, build_prompt_context


def test_preprocess_output_candidates() -> None:
    text = "Show that for any real x, x + 1/x >= 2."
    output = build_preprocess_output(text)

    assert output.text == text
    assert hasattr(output, "cue_candidates")
    assert hasattr(output, "math_candidates")

    cues = [(c.category, c.start, c.end, c.text) for c in output.cue_candidates]
    assert cues == [
        ("VERB_PROVE", 0, 9, "Show that"),
        ("PHRASE_QUANTIFIER", 10, 17, "for any"),
    ]

    math = [(c.kind, c.start, c.end, c.text) for c in output.math_candidates]
    assert math == [
        ("inline_math", 23, 24, "x"),
        ("inline_math", 26, 27, "x"),
        ("inline_math", 30, 31, "1"),
        ("inline_math", 32, 33, "x"),
        ("inline_math", 37, 38, "2"),
    ]

    for candidate in output.cue_candidates:
        assert text[candidate.start : candidate.end] == candidate.text
        assert candidate.category in {
            "VERB_PROVE",
            "VERB_FIND",
            "VERB_COMPUTE",
            "PHRASE_ASSUME",
            "PHRASE_LET",
            "PHRASE_QUANTIFIER",
            "PHRASE_CONSTRAINT",
        }

    for candidate in output.math_candidates:
        assert text[candidate.start : candidate.end] == candidate.text
        assert candidate.kind == "inline_math"


def test_preprocess_output_dict_keys() -> None:
    text = "Find x."
    payload = build_preprocess_output(text).to_dict()

    assert "cues" not in payload
    assert "math" not in payload
    assert "cue_candidates" in payload
    assert "math_candidates" in payload


def test_build_prompt_context_keys_and_spans() -> None:
    text = "Show that x = 2. Find y."
    pre = {
        "text": text,
        "math_candidates": [
            {"start": 10, "end": 11, "text": "x"},
            {"start": 14, "end": 15, "text": "2"},
            {"start": 22, "end": 23, "text": "y"},
        ],
        "cue_candidates": [
            {"start": 0, "end": 9, "text": "Show that", "category": "VERB_PROVE"},
            {"start": 17, "end": 21, "text": "Find", "category": "VERB_FIND"},
        ],
    }

    context = build_prompt_context(pre)

    assert set(context.keys()) == {
        "text",
        "sentences",
        "math_candidates",
        "cue_candidates",
        "instructions",
    }
    assert context["text"] == text

    for sentence in context["sentences"]:
        assert text[sentence["start"] : sentence["end"]] == sentence["text"]
        assert sentence["span_id"].startswith("s")

    for candidate in context["math_candidates"]:
        assert text[candidate["start"] : candidate["end"]] == candidate["text"]
        assert candidate["span_id"].startswith("m")

    for candidate in context["cue_candidates"]:
        assert text[candidate["start"] : candidate["end"]] == candidate["text"]
        assert candidate["span_id"].startswith("c")
        assert candidate["cue"] in {"VERB_PROVE", "VERB_FIND"}


def test_build_prompt_context_deterministic_order() -> None:
    text = "Let x be real. Compute 2x."
    pre = {
        "text": text,
        "math_candidates": [
            {"start": 21, "end": 22, "text": "2"},
            {"start": 22, "end": 23, "text": "x"},
            {"start": 4, "end": 5, "text": "x"},
        ],
        "cue_candidates": [
            {"start": 0, "end": 3, "text": "Let", "category": "PHRASE_LET"},
            {"start": 13, "end": 20, "text": "Compute", "category": "VERB_COMPUTE"},
        ],
    }

    context = build_prompt_context(pre)

    math_ids = [span["span_id"] for span in context["math_candidates"]]
    cue_ids = [span["span_id"] for span in context["cue_candidates"]]

    assert math_ids == ["m1", "m2", "m3"]
    assert cue_ids == ["c1", "c2"]
