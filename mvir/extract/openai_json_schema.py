"""OpenAI-compatible strict JSON schema subset for MVIR v0.1."""

from __future__ import annotations

from copy import deepcopy


def _expr_schema() -> dict:
    """Recursive Expr schema using strict tagged union variants."""

    expr_ref = {"$ref": "#/$defs/Expr"}

    symbol = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "node": {"const": "Symbol", "type": "string"},
            "id": {"type": "string"},
        },
        "required": ["node", "id"],
    }
    number = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "node": {"const": "Number", "type": "string"},
            "value": {"type": "number"},
        },
        "required": ["node", "value"],
    }
    bool_node = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "node": {"type": "string", "enum": ["Bool", "True", "False"]},
            "value": {"type": "boolean"},
        },
        "required": ["node", "value"],
    }
    add = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "node": {"const": "Add", "type": "string"},
            "args": {"type": "array", "items": expr_ref},
        },
        "required": ["node", "args"],
    }
    mul = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "node": {"const": "Mul", "type": "string"},
            "args": {"type": "array", "items": expr_ref},
        },
        "required": ["node", "args"],
    }
    div = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "node": {"const": "Div", "type": "string"},
            "num": expr_ref,
            "den": expr_ref,
        },
        "required": ["node", "num", "den"],
    }
    pow_node = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "node": {"const": "Pow", "type": "string"},
            "base": expr_ref,
            "exp": expr_ref,
        },
        "required": ["node", "base", "exp"],
    }
    neg = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "node": {"const": "Neg", "type": "string"},
            "arg": expr_ref,
        },
        "required": ["node", "arg"],
    }

    def _rel(rel_node: str) -> dict:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "node": {"const": rel_node, "type": "string"},
                "lhs": expr_ref,
                "rhs": expr_ref,
            },
            "required": ["node", "lhs", "rhs"],
        }

    sum_node = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "node": {"const": "Sum", "type": "string"},
            "var": {"type": "string"},
            "from": expr_ref,
            "to": expr_ref,
            "body": expr_ref,
        },
        "required": ["node", "var", "from", "to", "body"],
    }
    call = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "node": {"const": "Call", "type": "string"},
            "fn": {"type": "string"},
            "args": {"type": "array", "items": expr_ref},
        },
        "required": ["node", "fn", "args"],
    }

    return {
        "$defs": {
            "Expr": {
                "oneOf": [
                    symbol,
                    number,
                    bool_node,
                    add,
                    mul,
                    div,
                    pow_node,
                    neg,
                    _rel("Eq"),
                    _rel("Neq"),
                    _rel("Lt"),
                    _rel("Le"),
                    _rel("Gt"),
                    _rel("Ge"),
                    _rel("Divides"),
                    sum_node,
                    call,
                ]
            }
        },
        "$ref": "#/$defs/Expr",
    }


def _span_ref_array_schema() -> dict:
    return {
        "type": "array",
        "items": {"type": "string"},
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
        "$defs": _expr_schema()["$defs"],
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
                        "expr": {"$ref": "#/$defs/Expr"},
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
                    "expr": {"$ref": "#/$defs/Expr"},
                    "trace": _span_ref_array_schema(),
                    "target": {"anyOf": [{"$ref": "#/$defs/Expr"}, {"type": "null"}]},
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
        },
    }
    return sanitize_openai_strict_schema(schema)
