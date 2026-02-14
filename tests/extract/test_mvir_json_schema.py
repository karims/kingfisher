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

