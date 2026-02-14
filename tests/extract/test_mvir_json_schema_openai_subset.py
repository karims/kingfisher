"""OpenAI-compatible subset tests for MVIR v0.1 JSON schema."""

from __future__ import annotations

import json

from mvir.extract.mvir_json_schema import get_mvir_v01_json_schema


def test_openai_subset_schema_has_no_oneof() -> None:
    schema = get_mvir_v01_json_schema()
    assert "oneOf" not in json.dumps(schema)


def test_openai_subset_schema_required_fields() -> None:
    schema = get_mvir_v01_json_schema()

    assumptions_required = schema["properties"]["assumptions"]["items"]["required"]
    entities_required = schema["properties"]["entities"]["items"]["required"]
    warnings_required = schema["properties"]["warnings"]["items"]["required"]
    goal_required = schema["properties"]["goal"]["required"]

    assert "kind" in assumptions_required
    assert "type" in entities_required
    assert "properties" in entities_required
    assert "code" in warnings_required
    assert "kind" in goal_required


def test_openai_subset_expr_fields_are_plain_objects() -> None:
    schema = get_mvir_v01_json_schema()
    assumptions_expr = schema["properties"]["assumptions"]["items"]["properties"]["expr"]
    goal_expr = schema["properties"]["goal"]["properties"]["expr"]

    assert assumptions_expr == {"type": "object"}
    assert goal_expr == {"type": "object"}

