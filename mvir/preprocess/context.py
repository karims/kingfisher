"""Prompt context scaffolding for preprocess outputs."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class CandidateSpan:
    """Span candidate detected by preprocess."""

    category: str
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class PreprocessOutput:
    """Structured output from preprocess suitable for prompt context."""

    text: str
    cue_candidates: list[CandidateSpan]
    math_candidates: list[CandidateSpan]

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict representation."""

        return {
            "text": self.text,
            "cue_candidates": [span.__dict__ for span in self.cue_candidates],
            "math_candidates": [span.__dict__ for span in self.math_candidates],
        }


_GOAL_VERB_RE = re.compile(
    r"\b(show|prove|find|compute|maximize|minimize|determine|solve)\b",
    re.IGNORECASE,
)
_QUANTIFIER_RE = re.compile(r"\b(for any|for all|there exists|exists)\b", re.IGNORECASE)
_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
_SYMBOL_RE = re.compile(r"\b[a-zA-Z]\b")


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
    cue_candidates.extend(_find_candidates(text, _GOAL_VERB_RE, "GOAL_VERB"))
    cue_candidates.extend(_find_candidates(text, _QUANTIFIER_RE, "QUANTIFIER"))
    cue_candidates = sorted(cue_candidates, key=lambda span: (span.start, span.end))

    math_candidates = []
    math_candidates.extend(_find_candidates(text, _NUMBER_RE, "MATH_TOKEN"))
    math_candidates.extend(_find_candidates(text, _SYMBOL_RE, "MATH_TOKEN"))
    math_candidates = sorted(math_candidates, key=lambda span: (span.start, span.end))

    return PreprocessOutput(
        text=text,
        cue_candidates=cue_candidates,
        math_candidates=math_candidates,
    )
