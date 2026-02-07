"""Extraction contract definitions for Phase 3.

Preprocess is lossless + offsets only; no semantic classification.
Phase 3 uses an LLM to produce MVIR semantics.
Providers must not modify MVIR schema.
"""

from __future__ import annotations

from mvir.core.models import MVIR


def validate_grounding_contract(mvir: MVIR) -> list[str]:
    """Validate grounding and reference integrity for MVIR."""

    errors: list[str] = []
    trace = mvir.trace
    trace_ids = {span.span_id for span in trace}

    if "s0" not in trace_ids:
        errors.append("Missing required span_id 's0' in trace.")
    if len(trace) < 2:
        errors.append("Trace must include s0 and at least one other span.")

    s0 = next((span for span in trace if span.span_id == "s0"), None)
    if s0 is not None:
        if s0.start != 0 or s0.end != len(mvir.source.text):
            errors.append("s0 span must cover the full source text.")

    for span in trace:
        expected = mvir.source.text[span.start : span.end]
        if span.text != expected:
            errors.append(f"Trace span '{span.span_id}' text mismatch.")

    referenced = set()
    for entity in mvir.entities:
        referenced.update(entity.trace)
    for assumption in mvir.assumptions:
        referenced.update(assumption.trace)
    referenced.update(mvir.goal.trace)
    for concept in mvir.concepts:
        referenced.update(concept.trace)
    for warning in mvir.warnings:
        referenced.update(warning.trace)

    unknown_refs = sorted(ref for ref in referenced if ref not in trace_ids)
    if unknown_refs:
        errors.append(f"Unknown trace ids referenced: {unknown_refs}")

    entity_ids = [entity.id for entity in mvir.entities]
    if len(entity_ids) != len(set(entity_ids)):
        errors.append("Entity ids must be unique.")

    if mvir.goal.kind == "compute" and mvir.goal.expr is None:
        errors.append("Compute goal requires an expr.")
    if mvir.goal.kind == "find" and mvir.goal.target is None:
        errors.append("Find goal requires a target.")

    return errors
