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
    "Top-level object MUST contain keys: meta, source, entities, assumptions, goal, concepts, warnings, trace.",
    "meta must include version=\"0.1\", id=PROBLEM_ID, and generator.",
    "source must include text equal to the exact full input text.",
    "entities.kind MUST be one of: variable, constant, function, set, sequence, point, vector, object.",
    "Do NOT use entity kinds like expression, equation, or inequality.",
    "Put equations/inequalities in assumptions.expr or goal.expr as AST nodes, not entities.kind.",
    "Expr MUST be node-based with discriminator key \"node\".",
    "DO NOT output {op,left,right} style trees.",
    "Symbol MUST include \"id\".",
    "Number MUST include \"value\".",
    "Pow MUST include \"base\" and \"exp\".",
    "Comparators (Eq/Neq/Lt/Le/Gt/Ge/Divides) MUST include \"lhs\" and \"rhs\".",
    "Never output placeholder nodes like {\"node\":\"Symbol\"} or {\"node\":\"Number\"}.",
    "x > 0 => {\"node\":\"Gt\",\"lhs\":{\"node\":\"Symbol\",\"id\":\"x\"},\"rhs\":{\"node\":\"Number\",\"value\":0}}",
    "x^2 >= 0 => {\"node\":\"Ge\",\"lhs\":{\"node\":\"Pow\",\"base\":{\"node\":\"Symbol\",\"id\":\"x\"},\"exp\":{\"node\":\"Number\",\"value\":2}},\"rhs\":{\"node\":\"Number\",\"value\":0}}",
    "Every entity, assumption, goal, concept, and warning MUST include trace referencing existing span_ids.",
    "entities[].trace / assumptions[].trace / goal.trace / concepts[].trace / warnings[].trace must be arrays of span_id strings ONLY, e.g. [\"s2\",\"s3\"].",
    "The span objects with start/end/text must exist ONLY in top-level trace.",
    "goal is ONE object. If multiple tasks appear, choose the primary goal and add a warning listing secondary tasks.",
    "If goal.kind is \"find\", you MUST include goal.target as an Expr node.",
    "If target cannot be extracted safely, DO NOT use goal.kind=\"find\"; use the nearest valid kind among compute/prove/exists and add warning code=\"goal_kind_downgraded\".",
    "Do NOT change trace spans or span_ids.",
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
        '    {"span_id":"s2","start":10,"end":18,"text":"x > 0.00"}',
        "  ],",
        '  "entities": [',
        '    {"id":"x","kind":"variable","type":"Real","trace":["s2"]}',
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
