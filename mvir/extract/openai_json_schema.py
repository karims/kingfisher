"""OpenAI-compatible strict JSON schema subset for MVIR v0.1."""

from __future__ import annotations

from copy import deepcopy


_EXPR_NODE_ENUM = [
    "Symbol",
    "Number",
    "Bool",
    "True",
    "False",
    "Add",
    "Mul",
    "Div",
    "Pow",
    "Neg",
    "Eq",
    "Neq",
    "Lt",
    "Le",
    "Gt",
    "Ge",
    "Divides",
    "Sum",
    "Call",
]


def _expr_ref_schema() -> dict:
    """Shallow nullable Expr reference shape for strict OpenAI schema."""

    return {
        "type": ["object", "null"],
        "additionalProperties": False,
        "properties": {
            "node": {"type": "string", "enum": _EXPR_NODE_ENUM},
        },
        "required": ["node"],
    }


def _expr_openai_superset_schema() -> dict:
    """Single-object Expr superset schema compatible with OpenAI strict mode."""

    props = {
        "node": {"type": "string", "enum": _EXPR_NODE_ENUM},
        "id": {"type": ["string", "null"]},
        "value": {"type": ["number", "boolean", "null"]},
        "lhs": _expr_ref_schema(),
        "rhs": _expr_ref_schema(),
        "args": {
            "type": ["array", "null"],
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "node": {"type": "string", "enum": _EXPR_NODE_ENUM},
                },
                "required": ["node"],
            },
        },
        "base": _expr_ref_schema(),
        "exp": _expr_ref_schema(),
        "num": _expr_ref_schema(),
        "den": _expr_ref_schema(),
        "arg": _expr_ref_schema(),
        "var": {"type": ["string", "null"]},
        "from": _expr_ref_schema(),
        "to": _expr_ref_schema(),
        "body": _expr_ref_schema(),
        "fn": {"type": ["string", "null"]},
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": props,
        "required": list(props.keys()),
    }


def _span_ref_array_schema() -> dict:
    return {
        "type": "array",
        "items": {"type": "string"},
    }


def _solver_event_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "event_id": {"type": "string"},
            "ts": {"type": ["string", "null"]},
            "kind": {
                "type": "string",
                "enum": [
                    "plan",
                    "claim",
                    "transform",
                    "tool_call",
                    "tool_result",
                    "branch",
                    "backtrack",
                    "final",
                    "note",
                    "error",
                ],
            },
            "message": {"type": "string"},
            "data": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "properties": {},
                "required": [],
            },
            "trace": {
                "type": ["array", "null"],
                "items": {"type": "string"},
            },
            "refs": {
                "type": ["array", "null"],
                "items": {"type": "string"},
            },
        },
        "required": ["event_id", "ts", "kind", "message", "data", "trace", "refs"],
    }


def _solver_trace_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "string", "const": "0.1"},
            "events": {"type": "array", "items": _solver_event_schema()},
            "summary": {"type": ["string", "null"]},
            "metrics": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "properties": {},
                "required": [],
            },
            "artifacts": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "properties": {},
                "required": [],
            },
        },
        "required": ["schema_version", "events", "summary", "metrics", "artifacts"],
    }


def sanitize_openai_strict_schema(schema: dict) -> dict:
    """Force OpenAI strict object-schema rules recursively.

    For object nodes with properties:
    - additionalProperties is set to False
    - required is set to all property keys (in insertion order)
    """

    def _walk(node):
        if isinstance(node, dict):
            schema_type = node.get("type")
            if schema_type == "object" and isinstance(node.get("properties"), dict):
                props = node["properties"]
                node["additionalProperties"] = False
                node["required"] = list(props.keys())

            if "properties" in node and isinstance(node["properties"], dict):
                for child in node["properties"].values():
                    _walk(child)
            if "items" in node:
                _walk(node["items"])
            if "$defs" in node and isinstance(node["$defs"], dict):
                for child in node["$defs"].values():
                    _walk(child)
            for key in ("anyOf", "oneOf", "allOf"):
                values = node.get(key)
                if isinstance(values, list):
                    for child in values:
                        _walk(child)
            if "discriminator" in node:
                _walk(node["discriminator"])
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    out = deepcopy(schema)
    _walk(out)
    return out


def get_mvir_v01_openai_json_schema() -> dict:
    """Return an OpenAI strict-mode compatible MVIR v0.1 schema subset."""

    schema = {
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
                    "required": ["id", "kind", "type", "properties", "trace"],
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
                    "required": ["expr", "kind", "trace", "id"],
                    "properties": {
                        "expr": _expr_openai_superset_schema(),
                        "kind": {"type": "string", "enum": ["given", "derived", "wlog"]},
                        "trace": _span_ref_array_schema(),
                        "id": {"type": ["string", "null"]},
                    },
                },
            },
            "goal": {
                "type": "object",
                "additionalProperties": False,
                "required": ["kind", "expr", "trace", "target"],
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
                    "expr": _expr_openai_superset_schema(),
                    "trace": _span_ref_array_schema(),
                    "target": _expr_ref_schema(),
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
                    "required": ["code", "message", "trace", "details"],
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
                    "required": ["span_id", "start", "end", "text"],
                    "properties": {
                        "span_id": {"type": "string"},
                        "start": {"type": "integer", "minimum": 0},
                        "end": {"type": "integer", "minimum": 0},
                        "text": {"type": ["string", "null"]},
                    },
                },
            },
            "solver_trace": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "properties": _solver_trace_schema()["properties"],
                "required": _solver_trace_schema()["required"],
            },
        },
    }
    out = sanitize_openai_strict_schema(schema)
    required = out.get("required")
    if isinstance(required, list):
        out["required"] = [key for key in required if key != "solver_trace"]
    return out
