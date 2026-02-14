"""JSON Schema helper for MVIR v0.1 structured outputs."""

from __future__ import annotations


def get_mvir_v01_json_schema() -> dict:
    """Return an OpenAI-compatible strict JSON Schema for MVIR v0.1."""

    entity_kinds = [
        "variable",
        "constant",
        "function",
        "set",
        "sequence",
        "point",
        "vector",
        "object",
    ]
    assumption_kinds = ["given", "derived", "wlog"]
    goal_kinds = [
        "prove",
        "find",
        "compute",
        "maximize",
        "minimize",
        "exists",
        "counterexample",
    ]
    concept_roles = [
        "domain",
        "pattern",
        "candidate_tool",
        "definition",
        "representation_hint",
    ]

    span_ref_array = {"type": "array", "items": {"type": "string"}}

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "MVIR v0.1",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "meta",
            "source",
            "entities",
            "assumptions",
            "goal",
            "concepts",
            "warnings",
            "trace",
        ],
        "properties": {
            "meta": {
                "type": "object",
                "additionalProperties": False,
                "required": ["version", "id", "generator", "created_at"],
                "properties": {
                    "version": {"type": "string", "const": "0.1"},
                    "id": {"type": "string"},
                    "generator": {"type": ["string", "null"]},
                    "created_at": {"type": ["string", "null"]},
                },
            },
            "source": {
                "type": "object",
                "additionalProperties": False,
                "required": ["text", "normalized_text", "spans"],
                "properties": {
                    "text": {"type": "string"},
                    "normalized_text": {"type": ["string", "null"]},
                    "spans": {
                        "type": ["array", "null"],
                        "items": {"type": "object"},
                    },
                },
            },
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "kind", "type", "properties", "trace"],
                    "properties": {
                        "id": {"type": "string"},
                        "kind": {"type": "string", "enum": entity_kinds},
                        "type": {"type": "string"},
                        "properties": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "trace": span_ref_array,
                    },
                },
            },
            "assumptions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["expr", "kind", "trace", "id"],
                    "properties": {
                        "expr": {"type": "object"},
                        "kind": {"type": "string", "enum": assumption_kinds},
                        "trace": span_ref_array,
                        "id": {"type": ["string", "null"]},
                    },
                },
            },
            "goal": {
                "type": "object",
                "additionalProperties": False,
                "required": ["kind", "expr", "target", "trace"],
                "properties": {
                    "kind": {"type": "string", "enum": goal_kinds},
                    "expr": {"type": "object"},
                    "target": {"type": ["object", "null"]},
                    "trace": span_ref_array,
                },
            },
            "concepts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "role", "trigger", "confidence", "trace", "name"],
                    "properties": {
                        "id": {"type": "string"},
                        "role": {"type": "string", "enum": concept_roles},
                        "trigger": {"type": ["string", "null"]},
                        "confidence": {"type": ["number", "null"]},
                        "trace": span_ref_array,
                        "name": {"type": ["string", "null"]},
                    },
                },
            },
            "warnings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["code", "message", "trace", "details"],
                    "properties": {
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                        "trace": span_ref_array,
                        "details": {"type": ["object", "null"]},
                    },
                },
            },
            "trace": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["span_id", "start", "end", "text"],
                    "properties": {
                        "span_id": {"type": "string"},
                        "start": {"type": "integer", "minimum": 0},
                        "end": {"type": "integer", "minimum": 0},
                        "text": {"type": ["string", "null"]},
                    },
                },
            },
        },
    }

    return schema
