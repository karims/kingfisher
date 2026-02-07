"""Prompt context scaffolding for preprocess outputs."""

from __future__ import annotations

from dataclasses import dataclass
import re

from mvir.preprocess.spans import detect_math_spans


@dataclass(frozen=True)
class CandidateSpan:
    """Span candidate detected by preprocess."""

    category: str
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class MathSpan:
    """Math span candidate without semantic classification."""

    start: int
    end: int
    text: str
    kind: str = "inline_math"


@dataclass(frozen=True)
class PreprocessOutput:
    """Structured output from preprocess suitable for prompt context."""

    text: str
    cue_candidates: list[CandidateSpan]
    math_candidates: list[MathSpan]

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict representation."""

        return {
            "text": self.text,
            "cue_candidates": [span.__dict__ for span in self.cue_candidates],
            "math_candidates": [span.__dict__ for span in self.math_candidates],
        }


_VERB_PROVE_RE = re.compile(r"\b(prove|show that)\b", re.IGNORECASE)
_VERB_FIND_RE = re.compile(r"\b(find|determine|solve for)\b", re.IGNORECASE)
_VERB_COMPUTE_RE = re.compile(r"\b(compute|simplify|evaluate)\b", re.IGNORECASE)
_PHRASE_ASSUME_RE = re.compile(r"\b(assume|given)\b", re.IGNORECASE)
_PHRASE_LET_RE = re.compile(r"\b(let)\b", re.IGNORECASE)
_PHRASE_QUANTIFIER_RE = re.compile(r"\b(for all|for any)\b", re.IGNORECASE)
_PHRASE_CONSTRAINT_RE = re.compile(r"\b(such that|satisfy)\b", re.IGNORECASE)


def _find_candidates(text: str, pattern: re.Pattern[str], category: str) -> list[CandidateSpan]:
    spans = []
    for match in pattern.finditer(text):
        spans.append(
            CandidateSpan(
                category=category,
                start=match.start(),
                end=match.end(),
                text=text[match.start() : match.end()],
            )
        )
    return spans


def build_preprocess_output(text: str) -> PreprocessOutput:
    """Build preprocess outputs with candidate spans only."""

    cue_candidates = []
    cue_candidates.extend(_find_candidates(text, _VERB_PROVE_RE, "VERB_PROVE"))
    cue_candidates.extend(_find_candidates(text, _VERB_FIND_RE, "VERB_FIND"))
    cue_candidates.extend(_find_candidates(text, _VERB_COMPUTE_RE, "VERB_COMPUTE"))
    cue_candidates.extend(_find_candidates(text, _PHRASE_ASSUME_RE, "PHRASE_ASSUME"))
    cue_candidates.extend(_find_candidates(text, _PHRASE_LET_RE, "PHRASE_LET"))
    cue_candidates.extend(_find_candidates(text, _PHRASE_QUANTIFIER_RE, "PHRASE_QUANTIFIER"))
    cue_candidates.extend(_find_candidates(text, _PHRASE_CONSTRAINT_RE, "PHRASE_CONSTRAINT"))
    cue_candidates = sorted(cue_candidates, key=lambda span: (span.start, span.end))

    math_candidates = [
        MathSpan(start=span["start"], end=span["end"], text=span["text"])
        for span in detect_math_spans(text)
    ]

    return PreprocessOutput(
        text=text,
        cue_candidates=cue_candidates,
        math_candidates=math_candidates,
    )


_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]?")


def _sorted_spans(spans: list[dict]) -> list[dict]:
    return sorted(spans, key=lambda span: (span["start"], span["end"]))


def build_prompt_context(pre: dict) -> dict:
    """Build a compact prompt context object from preprocess output."""

    text = pre.get("text", "")
    sentences = []
    sentence_id = 1
    for match in _SENTENCE_RE.finditer(text):
        start = match.start()
        end = match.end()
        snippet = text[start:end]
        if not snippet.strip():
            continue
        sentences.append(
            {
                "span_id": f"s{sentence_id}",
                "start": start,
                "end": end,
                "text": snippet,
            }
        )
        sentence_id += 1

    math_candidates = []
    math_id = 1
    for span in _sorted_spans(pre.get("math_candidates", [])):
        math_candidates.append(
            {
                "span_id": f"m{math_id}",
                "start": span["start"],
                "end": span["end"],
                "text": span["text"],
            }
        )
        math_id += 1

    cue_candidates = []
    cue_id = 1
    for span in _sorted_spans(pre.get("cue_candidates", [])):
        cue = span.get("cue") or span.get("category") or span.get("label")
        cue_candidates.append(
            {
                "span_id": f"c{cue_id}",
                "start": span["start"],
                "end": span["end"],
                "text": span["text"],
                "cue": cue,
            }
        )
        cue_id += 1

    return {
        "text": text,
        "sentences": sentences,
        "math_candidates": math_candidates,
        "cue_candidates": cue_candidates,
        "instructions": {
            "must_reference_spans": True,
            "output_format": "MVIR_JSON",
            "no_freeform_text": True,
        },
    }
