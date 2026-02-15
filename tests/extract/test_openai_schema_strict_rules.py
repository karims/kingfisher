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
    expr_schema = schema["$defs"]["Expr"]
    assert "oneOf" in expr_schema
    variants = expr_schema["oneOf"]
    assert isinstance(variants, list)
    assert len(variants) > 0

    for variant in variants:
        assert variant["type"] == "object"
        assert variant["additionalProperties"] is False
        assert set(variant["required"]) == set(variant["properties"].keys())

    symbol_variant = next(
        v for v in variants if v["properties"].get("node", {}).get("const") == "Symbol"
    )
    assert set(symbol_variant["required"]) == {"node", "id"}

    gt_variant = next(
        v for v in variants if v["properties"].get("node", {}).get("const") == "Gt"
    )
    assert set(gt_variant["required"]) == {"node", "lhs", "rhs"}
