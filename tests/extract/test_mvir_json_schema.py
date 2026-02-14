"""Tests for MVIR v0.1 JSON schema helper."""

from __future__ import annotations

from mvir.extract.mvir_json_schema import get_mvir_v01_json_schema


def test_mvir_json_schema_required_top_level_keys() -> None:
    schema = get_mvir_v01_json_schema()
    required = set(schema["required"])
    assert {
        "meta",
        "source",
        "entities",
        "assumptions",
        "goal",
        "concepts",
        "warnings",
        "trace",
    }.issubset(required)


def test_mvir_json_schema_entities_trace_is_array_of_strings() -> None:
    schema = get_mvir_v01_json_schema()
    entities = schema["properties"]["entities"]["items"]["properties"]
    trace_schema = entities["trace"]
    assert trace_schema["type"] == "array"
    assert trace_schema["items"]["type"] == "string"


def test_mvir_json_schema_goal_is_object() -> None:
    schema = get_mvir_v01_json_schema()
    goal_schema = schema["properties"]["goal"]
    assert goal_schema["type"] == "object"


def test_mvir_json_schema_warnings_require_code() -> None:
    schema = get_mvir_v01_json_schema()
    warnings_required = schema["properties"]["warnings"]["items"]["required"]
    assert "code" in warnings_required


def test_mvir_json_schema_assumptions_require_kind() -> None:
    schema = get_mvir_v01_json_schema()
    assumptions_required = schema["properties"]["assumptions"]["items"]["required"]
    assert "kind" in assumptions_required


def test_mvir_json_schema_expr_uses_node_discriminator_and_forbids_op() -> None:
    schema = get_mvir_v01_json_schema()
    expr_schema = schema["$defs"]["Expr"]
    assert expr_schema["discriminator"]["propertyName"] == "node"
    symbol_schema = schema["$defs"]["Symbol"]
    assert "node" in symbol_schema["required"]
    assert symbol_schema["additionalProperties"] is False
    assert "op" not in symbol_schema["properties"]
