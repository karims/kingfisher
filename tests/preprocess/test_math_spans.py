"""Tests for math span detection."""

from __future__ import annotations

from mvir.preprocess.spans import detect_math_spans


def test_detect_math_spans_amc12a_2015_p10() -> None:
    text = "Integers x > y > 0 satisfy x + y + xy = 80. Find x."
    spans = detect_math_spans(text)

    expected = {
        "x > y > 0": (9, 18),
        "x + y + xy = 80": (27, 42),
    }
    found = {span["text"]: (span["start"], span["end"]) for span in spans}

    for snippet, (start, end) in expected.items():
        assert snippet in found
        assert found[snippet] == (start, end)
        assert text[start:end] == snippet


def test_detect_math_spans_inline_dollar() -> None:
    text = "Compute $x^2 + 1$."
    spans = detect_math_spans(text)
    found = {span["text"]: (span["start"], span["end"]) for span in spans}

    assert "x^2 + 1" in found
    start, end = found["x^2 + 1"]
    assert (start, end) == (9, 16)
    assert text[start:end] == "x^2 + 1"


def test_detect_math_spans_latex_parens_brackets() -> None:
    text = r"Let \(x>0\) and \[x^2=1\]."
    spans = detect_math_spans(text)
    found = {span["text"]: (span["start"], span["end"]) for span in spans}

    assert "x>0" in found
    assert "x^2=1" in found
    start, end = found["x>0"]
    assert (start, end) == (6, 9)
    assert text[start:end] == "x>0"
    start, end = found["x^2=1"]
    assert (start, end) == (18, 23)
    assert text[start:end] == "x^2=1"


def test_detect_math_spans_block_dollar() -> None:
    text = r"$$\sum_{k=1}^n k$$"
    spans = detect_math_spans(text)
    found = {span["text"]: (span["start"], span["end"]) for span in spans}

    assert r"\sum_{k=1}^n k" in found
    start, end = found[r"\sum_{k=1}^n k"]
    assert (start, end) == (2, 16)
    assert text[start:end] == r"\sum_{k=1}^n k"
