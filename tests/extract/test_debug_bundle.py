"""Tests for formalize debug bundle generation on failure."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mvir.extract.formalize import formalize_text_to_mvir
from mvir.extract.providers.mock import MockProvider


def test_debug_bundle_written_on_json_parse_failure(tmp_path: Path) -> None:
    provider = MockProvider({"bad_case": "{not-json}"})
    debug_dir = tmp_path / "debug"

    with pytest.raises(ValueError) as excinfo:
        formalize_text_to_mvir(
            "x",
            provider,
            problem_id="bad_case",
            strict=True,
            debug_dir=str(debug_dir),
        )

    assert "JSON parse failed" in str(excinfo.value)

    bundle = debug_dir / "bad_case"
    assert (bundle / "source.txt").exists()
    assert (bundle / "preprocess.json").exists()
    assert (bundle / "prompt.txt").exists()
    assert (bundle / "raw_output.txt").exists()
    assert (bundle / "error.txt").exists()

    assert (bundle / "source.txt").read_text(encoding="utf-8") == "x"

    preprocess_payload = json.loads(
        (bundle / "preprocess.json").read_text(encoding="utf-8")
    )
    assert preprocess_payload["text"] == "x"

    prompt_text = (bundle / "prompt.txt").read_text(encoding="utf-8")
    assert "PROBLEM_ID=bad_case" in prompt_text

    raw_output = (bundle / "raw_output.txt").read_text(encoding="utf-8")
    assert raw_output == "{not-json}"

    error_text = (bundle / "error.txt").read_text(encoding="utf-8")
    assert "kind: json_parse" in error_text
    assert "JSON parse failed" in error_text

