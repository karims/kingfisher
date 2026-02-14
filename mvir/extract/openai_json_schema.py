"""OpenAI-compatible strict JSON schema subset for MVIR v0.1."""

from __future__ import annotations


def _expr_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["node"],
        "properties": {
            "node": {"type": "string"},
        },
    }


def _span_ref_array_schema() -> dict:
    return {
        "type": "array",
        "items": {"type": "string"},
    }


def get_mvir_v01_openai_json_schema() -> dict:
    """Return an OpenAI strict-mode compatible MVIR v0.1 schema subset."""

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "MVIR v0.1 OpenAI Subset",
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
                "required": ["version", "id"],
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
                "required": ["text"],
                "properties": {
                    "text": {"type": "string"},
                    "normalized_text": {"type": ["string", "null"]},
                    "spans": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {},
                            "required": [],
                        },
                    },
                },
            },
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "kind", "type"],
                    "properties": {
                        "id": {"type": "string"},
                        "kind": {
                            "type": "string",
                            "enum": [
                                "variable",
                                "constant",
                                "function",
                                "set",
                                "sequence",
                                "point",
                                "vector",
                                "object",
                            ],
                        },
                        "type": {"type": "string"},
                        "properties": {"type": "array", "items": {"type": "string"}},
                        "trace": _span_ref_array_schema(),
                    },
                },
            },
            "assumptions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["expr", "kind"],
                    "properties": {
                        "expr": _expr_schema(),
                        "kind": {"type": "string", "enum": ["given", "derived", "wlog"]},
                        "trace": _span_ref_array_schema(),
                        "id": {"type": ["string", "null"]},
                    },
                },
            },
            "goal": {
                "type": "object",
                "additionalProperties": False,
                "required": ["kind", "expr"],
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": [
                            "prove",
                            "find",
                            "compute",
                            "maximize",
                            "minimize",
                            "exists",
                            "counterexample",
                        ],
                    },
                    "expr": _expr_schema(),
                    "trace": _span_ref_array_schema(),
                    "target": {
                        "type": ["object", "null"],
                        "additionalProperties": False,
                        "required": ["node"],
                        "properties": {
                            "node": {"type": "string"},
                        },
                    },
                },
            },
            "concepts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "role"],
                    "properties": {
                        "id": {"type": "string"},
                        "role": {
                            "type": "string",
                            "enum": [
                                "domain",
                                "pattern",
                                "candidate_tool",
                                "definition",
                                "representation_hint",
                            ],
                        },
                        "trigger": {"type": ["string", "null"]},
                        "confidence": {"type": ["number", "null"]},
                        "trace": _span_ref_array_schema(),
                        "name": {"type": ["string", "null"]},
                    },
                },
            },
            "warnings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["code", "message"],
                    "properties": {
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                        "trace": _span_ref_array_schema(),
                        "details": {
                            "type": ["object", "null"],
                            "additionalProperties": False,
                            "properties": {},
                            "required": [],
                        },
                    },
                },
            },
            "trace": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["span_id", "start", "end"],
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

