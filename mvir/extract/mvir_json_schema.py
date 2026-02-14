"""JSON Schema helper for MVIR v0.1 structured outputs."""

from __future__ import annotations


def get_mvir_v01_json_schema() -> dict:
    """Return a strict JSON Schema aligned with current MVIR v0.1 models."""

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

    expr_ref = {"$ref": "#/$defs/Expr"}

    expr_defs = {
        "Symbol": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "id"],
            "properties": {
                "node": {"const": "Symbol", "type": "string"},
                "id": {"type": "string"},
            },
        },
        "Number": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "value"],
            "properties": {
                "node": {"const": "Number", "type": "string"},
                "value": {"type": "number"},
            },
        },
        "Bool": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "value"],
            "properties": {
                "node": {"type": "string", "enum": ["Bool", "True", "False"]},
                "value": {"type": "boolean"},
            },
        },
        "Add": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "args"],
            "properties": {
                "node": {"const": "Add", "type": "string"},
                "args": {"type": "array", "minItems": 1, "items": expr_ref},
            },
        },
        "Mul": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "args"],
            "properties": {
                "node": {"const": "Mul", "type": "string"},
                "args": {"type": "array", "minItems": 1, "items": expr_ref},
            },
        },
        "Div": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "num", "den"],
            "properties": {
                "node": {"const": "Div", "type": "string"},
                "num": expr_ref,
                "den": expr_ref,
            },
        },
        "Pow": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "base", "exp"],
            "properties": {
                "node": {"const": "Pow", "type": "string"},
                "base": expr_ref,
                "exp": expr_ref,
            },
        },
        "Neg": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "arg"],
            "properties": {
                "node": {"const": "Neg", "type": "string"},
                "arg": expr_ref,
            },
        },
        "Eq": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "lhs", "rhs"],
            "properties": {
                "node": {"const": "Eq", "type": "string"},
                "lhs": expr_ref,
                "rhs": expr_ref,
            },
        },
        "Neq": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "lhs", "rhs"],
            "properties": {
                "node": {"const": "Neq", "type": "string"},
                "lhs": expr_ref,
                "rhs": expr_ref,
            },
        },
        "Lt": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "lhs", "rhs"],
            "properties": {
                "node": {"const": "Lt", "type": "string"},
                "lhs": expr_ref,
                "rhs": expr_ref,
            },
        },
        "Le": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "lhs", "rhs"],
            "properties": {
                "node": {"const": "Le", "type": "string"},
                "lhs": expr_ref,
                "rhs": expr_ref,
            },
        },
        "Gt": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "lhs", "rhs"],
            "properties": {
                "node": {"const": "Gt", "type": "string"},
                "lhs": expr_ref,
                "rhs": expr_ref,
            },
        },
        "Ge": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "lhs", "rhs"],
            "properties": {
                "node": {"const": "Ge", "type": "string"},
                "lhs": expr_ref,
                "rhs": expr_ref,
            },
        },
        "Divides": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "lhs", "rhs"],
            "properties": {
                "node": {"const": "Divides", "type": "string"},
                "lhs": expr_ref,
                "rhs": expr_ref,
            },
        },
        "Sum": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "var", "from", "to", "body"],
            "properties": {
                "node": {"const": "Sum", "type": "string"},
                "var": {"type": "string"},
                "from": expr_ref,
                "to": expr_ref,
                "body": expr_ref,
            },
        },
        "Call": {
            "type": "object",
            "additionalProperties": False,
            "required": ["node", "fn", "args"],
            "properties": {
                "node": {"const": "Call", "type": "string"},
                "fn": {"type": "string"},
                "args": {"type": "array", "items": expr_ref},
            },
        },
    }

    expr_one_of = [
        {"$ref": "#/$defs/Symbol"},
        {"$ref": "#/$defs/Number"},
        {"$ref": "#/$defs/Bool"},
        {"$ref": "#/$defs/Add"},
        {"$ref": "#/$defs/Mul"},
        {"$ref": "#/$defs/Div"},
        {"$ref": "#/$defs/Pow"},
        {"$ref": "#/$defs/Neg"},
        {"$ref": "#/$defs/Eq"},
        {"$ref": "#/$defs/Neq"},
        {"$ref": "#/$defs/Lt"},
        {"$ref": "#/$defs/Le"},
        {"$ref": "#/$defs/Gt"},
        {"$ref": "#/$defs/Ge"},
        {"$ref": "#/$defs/Divides"},
        {"$ref": "#/$defs/Sum"},
        {"$ref": "#/$defs/Call"},
    ]

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "MVIR v0.1",
        "type": "object",
        "$defs": {
            "Expr": {
                "oneOf": expr_one_of,
                "discriminator": {"propertyName": "node"},
            },
            **expr_defs,
        },
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
                    "required": ["expr", "kind", "trace"],
                    "properties": {
                        "expr": expr_ref,
                        "kind": {"type": "string", "enum": assumption_kinds},
                        "trace": span_ref_array,
                        "id": {"type": ["string", "null"]},
                    },
                },
            },
            "goal": {
                "type": "object",
                "additionalProperties": False,
                "required": ["kind", "expr", "trace"],
                "properties": {
                    "kind": {"type": "string", "enum": goal_kinds},
                    "expr": expr_ref,
                    "target": {"type": ["object", "null"]},
                    "trace": span_ref_array,
                },
            },
            "concepts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "role", "trace"],
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
                    "required": ["code", "message", "trace"],
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

    return schema
