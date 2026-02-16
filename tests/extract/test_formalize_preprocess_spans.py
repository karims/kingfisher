"""Regression tests for preprocess spans flowing into formalize prompt context."""

from __future__ import annotations

import json
from pathlib import Path

from mvir.extract.context import build_prompt_context
from mvir.extract.formalize import formalize_text_to_mvir
from mvir.extract.providers.mock import MockProvider
from mvir.preprocess.context import build_preprocess_output


def test_preprocess_latex_smoke_prompt_context_has_sentences() -> None:
    problem_path = Path("examples/problems/latex_smoke_01.txt")
    text = problem_path.read_text(encoding="utf-8")

    pre = build_preprocess_output(text)
    context = build_prompt_context(pre.to_dict())

    assert context["sentences"]
    assert context["sentences"][0]["span_id"].startswith("s")


def test_formalize_with_mock_provider_keeps_non_empty_trace() -> None:
    problem_path = Path("examples/problems/latex_smoke_01.txt")
    text = problem_path.read_text(encoding="utf-8")
    pre = build_preprocess_output(text)
    context = build_prompt_context(pre.to_dict())

    trace = [
        {
            "span_id": "s0",
            "start": 0,
            "end": len(text),
            "text": text,
        }
    ]
    for sentence in context["sentences"]:
        trace.append(
            {
                "span_id": sentence["span_id"],
                "start": sentence["start"],
                "end": sentence["end"],
                "text": sentence["text"],
            }
        )

    goal_trace_id = context["sentences"][0]["span_id"] if context["sentences"] else "s0"
    payload = {
        "meta": {"version": "0.1", "id": "latex_smoke_01", "generator": "mock"},
        "source": {"text": text},
        "entities": [],
        "assumptions": [],
        "goal": {
            "kind": "prove",
            "expr": {"node": "Bool", "value": True},
            "trace": [goal_trace_id],
        },
        "concepts": [],
        "warnings": [],
        "trace": trace,
    }
    provider = MockProvider({"latex_smoke_01": json.dumps(payload)})

    mvir = formalize_text_to_mvir(text, provider, problem_id="latex_smoke_01")

    assert mvir.trace
    assert len(mvir.trace) >= 1
