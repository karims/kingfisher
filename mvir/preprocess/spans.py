"""Preprocess span detection utilities."""

from __future__ import annotations

import re

_OPERATOR_CHARS = set("=<>+*/^≤≥≠×÷")
_BRACKET_CHARS = set("()[]{}")
_BOUNDARY_WORD_RE = re.compile(
    r"\b(assume|given|let|show|prove|find|compute|simplify|evaluate|determine|solve|"
    r"such|that|satisfy|for|any|all|integer|integers|real|rational|natural|complex)\b",
    re.IGNORECASE,
)


def _is_allowed_char(ch: str) -> bool:
    if ch.isalpha() or ch.isdigit() or ch == "_":
        return True
    if ch.isspace():
        return True
    if ch in _OPERATOR_CHARS or ch in _BRACKET_CHARS:
        return True
    return False


def _looks_math_like(text: str) -> bool:
    if any(ch in _OPERATOR_CHARS for ch in text):
        return True
    if any(ch in _BRACKET_CHARS for ch in text):
        tokens = re.findall(r"[A-Za-z]+|\d+(?:\.\d+)?", text)
        if len(tokens) >= 2:
            return True
    return False


def _trim_span(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _split_on_boundaries(text: str, start: int, end: int) -> list[tuple[int, int]]:
    run_text = text[start:end]
    segments: list[tuple[int, int]] = []
    cursor = 0
    for match in _BOUNDARY_WORD_RE.finditer(run_text):
        seg_start = cursor
        seg_end = match.start()
        if seg_end > seg_start:
            segments.append((start + seg_start, start + seg_end))
        cursor = match.end()
    if cursor < len(run_text):
        segments.append((start + cursor, end))
    return segments


def _dedupe_spans(spans: list[dict]) -> list[dict]:
    unique = {}
    for span in spans:
        key = (span["start"], span["end"])
        if key not in unique:
            unique[key] = span

    sorted_spans = sorted(unique.values(), key=lambda span: (span["start"], -span["end"]))
    kept: list[dict] = []
    for span in sorted_spans:
        if any(
            span["start"] >= other["start"] and span["end"] <= other["end"]
            for other in kept
        ):
            continue
        kept.append(span)
    return sorted(kept, key=lambda span: (span["start"], span["end"]))


def _detect_latex_spans(text: str) -> list[dict]:
    spans = []
    idx = 0
    length = len(text)
    while idx < length:
        if text.startswith("$$", idx):
            end = text.find("$$", idx + 2)
            if end != -1:
                start = idx + 2
                spans.append(
                    {
                        "start": start,
                        "end": end,
                        "text": text[start:end],
                        "kind": "inline_math",
                    }
                )
                idx = end + 2
                continue
        if text.startswith("\\(", idx):
            end = text.find("\\)", idx + 2)
            if end != -1:
                start = idx + 2
                spans.append(
                    {
                        "start": start,
                        "end": end,
                        "text": text[start:end],
                        "kind": "inline_math",
                    }
                )
                idx = end + 2
                continue
        if text.startswith("\\[", idx):
            end = text.find("\\]", idx + 2)
            if end != -1:
                start = idx + 2
                spans.append(
                    {
                        "start": start,
                        "end": end,
                        "text": text[start:end],
                        "kind": "inline_math",
                    }
                )
                idx = end + 2
                continue
        if text.startswith("$", idx):
            end = text.find("$", idx + 1)
            if end != -1:
                start = idx + 1
                spans.append(
                    {
                        "start": start,
                        "end": end,
                        "text": text[start:end],
                        "kind": "inline_math",
                    }
                )
                idx = end + 1
                continue
        idx += 1
    return spans


def detect_math_spans(text: str) -> list[dict]:
    """Detect contiguous math-like spans using a character scan."""

    runs = []
    start = None
    for idx, ch in enumerate(text):
        if _is_allowed_char(ch):
            if start is None:
                start = idx
        elif start is not None:
            runs.append((start, idx))
            start = None
    if start is not None:
        runs.append((start, len(text)))

    spans = []
    for run_start, run_end in runs:
        if run_start > 0 and text[run_start] in "([" and text[run_start - 1] == "\\":
            run_start += 1
        if run_start >= run_end:
            continue
        for seg_start, seg_end in _split_on_boundaries(text, run_start, run_end):
            trimmed_start, trimmed_end = _trim_span(text, seg_start, seg_end)
            if trimmed_start >= trimmed_end:
                continue
            snippet = text[trimmed_start:trimmed_end]
            if not _looks_math_like(snippet):
                continue
            spans.append(
                {
                    "start": trimmed_start,
                    "end": trimmed_end,
                    "text": snippet,
                    "kind": "inline_math",
                }
            )

    spans.extend(_detect_latex_spans(text))
    return _dedupe_spans(spans)
