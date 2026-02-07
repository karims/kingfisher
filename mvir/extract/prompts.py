"""Prompt templates for Phase 3 extraction.

Preprocess is lossless + offsets only; no semantic classification.
Phase 3 uses an LLM to produce MVIR semantics.
Providers must not modify MVIR schema.
"""

from __future__ import annotations

import json


_INSTRUCTIONS = [
    "Output MUST be valid JSON only (no markdown, no prose).",
    "Output MUST conform to MVIR v0.1 schema.",
    "Every entity, assumption, goal, concept, and warning MUST include trace referencing existing span_ids.",
    "Trace spans must include start/end offsets.",
    "If unsure about a sentence, DO NOT invent meaning.",
    "Do not invent assumptions or goals.",
    "Keep such sentences only as context via trace.",
    "Preserve original meaning; do not introduce new variables silently.",
]


_TRACE_EXAMPLE = "\n".join(
    [
        "{",
        '  "trace": [',
        '    {"span_id": "s0", "start": 0, "end": 5}',
        "  ],",
        '  "entities": [',
        '    {"id": "x", "kind": "variable", "type": "Real", "trace": ["s0"]}',
        "  ]",
        "}",
    ]
)


def build_mvir_prompt(prompt_context: dict, *, problem_id: str) -> str:
    """Build provider prompt text from context."""

    context_json = json.dumps(prompt_context, ensure_ascii=False)
    lines = [
        "SYSTEM INSTRUCTIONS:",
        *_INSTRUCTIONS,
        "",
        "JSON TRACE EXAMPLE:",
        _TRACE_EXAMPLE,
        "",
        f"PROBLEM_ID={problem_id}",
        "",
        "PROMPT_CONTEXT_JSON:",
        context_json,
    ]
    return "\n".join(lines)
