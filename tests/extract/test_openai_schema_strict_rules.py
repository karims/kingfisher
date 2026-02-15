"""Strict OpenAI JSON schema rule checks for MVIR subset schema."""

from __future__ import annotations

from mvir.extract.openai_json_schema import (
    get_mvir_v01_openai_json_schema,
    sanitize_openai_strict_schema,
)


def _walk_schema_nodes(node):
    if isinstance(node, dict):
        yield node
        if "properties" in node and isinstance(node["properties"], dict):
            for child in node["properties"].values():
                yield from _walk_schema_nodes(child)
        if "items" in node:
            yield from _walk_schema_nodes(node["items"])
        for key in ("anyOf", "oneOf", "allOf"):
            if key in node and isinstance(node[key], list):
                for child in node[key]:
                    yield from _walk_schema_nodes(child)
        if "$defs" in node and isinstance(node["$defs"], dict):
            for child in node["$defs"].values():
                yield from _walk_schema_nodes(child)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_schema_nodes(item)


def test_openai_schema_object_required_matches_properties_exactly() -> None:
    schema = get_mvir_v01_openai_json_schema()
    for node in _walk_schema_nodes(schema):
        if not isinstance(node, dict):
            continue
        if node.get("type") == "object" and "properties" in node:
            properties = node["properties"]
            assert isinstance(properties, dict)
            assert node.get("additionalProperties") is False
            assert "required" in node
            required = node["required"]
            assert isinstance(required, list)
            assert set(required) == set(properties.keys())


def test_sanitize_openai_strict_schema_repairs_broken_object_schema() -> None:
    broken = {
        "type": "object",
        "properties": {
            "a": {"type": "string"},
            "b": {
                "type": "object",
                "properties": {"x": {"type": "integer"}},
            },
        },
        "required": ["a"],
    }
    fixed = sanitize_openai_strict_schema(broken)

    assert fixed["additionalProperties"] is False
    assert fixed["required"] == ["a", "b"]
    assert fixed["properties"]["b"]["additionalProperties"] is False
    assert fixed["properties"]["b"]["required"] == ["x"]


def test_openai_expr_schema_uses_node_enum() -> None:
    schema = get_mvir_v01_openai_json_schema()
    assumptions_expr = schema["properties"]["assumptions"]["items"]["properties"]["expr"]
    goal_expr = schema["properties"]["goal"]["properties"]["expr"]
    goal_target = schema["properties"]["goal"]["properties"]["target"]

    for expr_schema in (assumptions_expr, goal_expr, goal_target):
        assert expr_schema["type"] == "object" or (
            isinstance(expr_schema["type"], list) and "object" in expr_schema["type"]
        )
        assert expr_schema["additionalProperties"] is False
        assert set(expr_schema["required"]) == set(expr_schema["properties"].keys())
        node = expr_schema["properties"]["node"]
        assert node["type"] == "string"
        assert isinstance(node["enum"], list)
        assert "Symbol" in node["enum"]
        assert "Gt" in node["enum"]


def test_openai_schema_core_objects_required_match_properties() -> None:
    schema = get_mvir_v01_openai_json_schema()
    objects = [
        schema["properties"]["meta"],
        schema["properties"]["source"],
        schema["properties"]["entities"]["items"],
        schema["properties"]["assumptions"]["items"],
        schema["properties"]["goal"],
        schema["properties"]["concepts"]["items"],
        schema["properties"]["warnings"]["items"],
        schema["properties"]["trace"]["items"],
    ]

    for obj in objects:
        assert obj["type"] == "object"
        assert obj["additionalProperties"] is False
        assert set(obj["required"]) == set(obj["properties"].keys())
