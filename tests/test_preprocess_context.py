"""Tests for preprocess context output."""

from __future__ import annotations

from mvir.preprocess.context import build_preprocess_output


def test_preprocess_output_candidates() -> None:
    text = "Show that for any real x, x + 1/x >= 2."
    output = build_preprocess_output(text)

    assert output.text == text
    assert hasattr(output, "cue_candidates")
    assert hasattr(output, "math_candidates")

    cues = [(c.category, c.start, c.end, c.text) for c in output.cue_candidates]
    assert cues == [
        ("GOAL_VERB", 0, 4, "Show"),
        ("QUANTIFIER", 10, 17, "for any"),
    ]

    math = [(c.category, c.start, c.end, c.text) for c in output.math_candidates]
    assert math == [
        ("MATH_TOKEN", 23, 24, "x"),
        ("MATH_TOKEN", 26, 27, "x"),
        ("MATH_TOKEN", 30, 31, "1"),
        ("MATH_TOKEN", 32, 33, "x"),
        ("MATH_TOKEN", 37, 38, "2"),
    ]

    for candidate in output.cue_candidates + output.math_candidates:
        assert text[candidate.start : candidate.end] == candidate.text
        assert candidate.category in {"GOAL_VERB", "QUANTIFIER", "MATH_TOKEN"}


def test_preprocess_output_dict_keys() -> None:
    text = "Find x."
    payload = build_preprocess_output(text).to_dict()

    assert "cues" not in payload
    assert "math" not in payload
    assert "cue_candidates" in payload
    assert "math_candidates" in payload
