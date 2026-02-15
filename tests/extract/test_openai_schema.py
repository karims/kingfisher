"""Tests for OpenAI-compatible MVIR JSON schema subset."""

from __future__ import annotations

import json

from mvir.extract.openai_json_schema import get_mvir_v01_openai_json_schema


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def _is_object_schema(schema_node: dict) -> bool:
    schema_type = schema_node.get("type")
    if schema_type == "object":
        return True
    if isinstance(schema_type, list) and "object" in schema_type:
        return True
    return False


def test_openai_schema_contains_expr_oneof() -> None:
    schema = get_mvir_v01_openai_json_schema()
    assert "oneOf" in json.dumps(schema)


def test_openai_schema_every_object_has_additional_properties_false() -> None:
    schema = get_mvir_v01_openai_json_schema()
    for node in _walk(schema):
        if not isinstance(node, dict):
            continue
        if _is_object_schema(node):
            assert "additionalProperties" in node
            assert node["additionalProperties"] is False


def test_openai_schema_is_json_serializable() -> None:
    schema = get_mvir_v01_openai_json_schema()
    dumped = json.dumps(schema)
    loaded = json.loads(dumped)
    assert isinstance(loaded, dict)


def test_openai_schema_trace_has_min_items_one() -> None:
    schema = get_mvir_v01_openai_json_schema()
    assert schema["properties"]["trace"]["minItems"] == 1
