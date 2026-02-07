"""Offline golden mock tests for MVIR grounding against preprocess spans."""

from __future__ import annotations

import json
from pathlib import Path

from mvir.core.models import MVIR
from mvir.extract.contract import validate_grounding_contract
from mvir.preprocess.context import build_preprocess_output, build_prompt_context


PROBLEM_IDS = [
    "latex_smoke_01",
    "mf2f_amc12a_2015_p10",
    "mf2f_algebra_2rootsintpoly_am10tap11eqasqpam110",
]


def _read_text_exact(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as f:
        return f.read()


def preprocess_text(text: str) -> list[dict]:
    """Return preprocess sentence spans as s1..sn."""

    pre = build_preprocess_output(text).to_dict()
    context = build_prompt_context(pre)
    return context["sentences"]


def _truncate(text: str, limit: int = 120) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _expected_trace(text: str) -> list[dict]:
    expected = [{"span_id": "s0", "start": 0, "end": len(text), "text": text}]
    expected.extend(preprocess_text(text))
    return expected


def _assert_span_equal(problem_id: str, expected: dict, actual: dict) -> None:
    span_id = expected["span_id"]
    assert actual["span_id"] == span_id, (
        f"[{problem_id}] span_id mismatch: expected={span_id!r} "
        f"actual={actual['span_id']!r}"
    )
    assert actual["start"] == expected["start"] and actual["end"] == expected["end"], (
        f"[{problem_id}] span {span_id} bounds mismatch: "
        f"expected=({expected['start']}, {expected['end']}) "
        f"actual=({actual['start']}, {actual['end']})"
    )
    assert actual.get("text", "") == expected["text"], (
        f"[{problem_id}] span {span_id} text mismatch: "
        f"expected={_truncate(expected['text'])!r} "
        f"actual={_truncate(actual.get('text', ''))!r}"
    )


def test_offline_golden_mock_mvir_grounding() -> None:
    root = Path(__file__).resolve().parents[2]
    mock_path = root / "examples" / "mock_llm" / "mock_responses.json"
    mock_payload = json.loads(_read_text_exact(mock_path))

    for problem_id in PROBLEM_IDS:
        text = _read_text_exact(root / "examples" / "problems" / f"{problem_id}.txt")
        expected_trace = _expected_trace(text)

        assert problem_id in mock_payload, f"Missing mock response key: {problem_id}"
        mvir_payload = json.loads(mock_payload[problem_id])
        mvir = MVIR.model_validate(mvir_payload)

        errors = validate_grounding_contract(mvir)
        assert errors == [], f"[{problem_id}] grounding errors: {errors}"
        assert mvir.source.text == text, f"[{problem_id}] source.text mismatch"

        actual_trace = [
            {
                "span_id": span.span_id,
                "start": span.start,
                "end": span.end,
                "text": span.text or "",
            }
            for span in mvir.trace
        ]

        expected_ids = [span["span_id"] for span in expected_trace]
        actual_ids = [span["span_id"] for span in actual_trace]
        assert actual_ids == expected_ids, (
            f"[{problem_id}] trace span_ids mismatch: "
            f"expected={expected_ids} actual={actual_ids}"
        )
        assert len(actual_trace) == len(expected_trace), (
            f"[{problem_id}] trace length mismatch: "
            f"expected={len(expected_trace)} actual={len(actual_trace)}"
        )

        for expected, actual in zip(expected_trace, actual_trace, strict=True):
            _assert_span_equal(problem_id, expected, actual)
