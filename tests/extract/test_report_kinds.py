"""Tests for failure kind classification and debug-path reporting."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pydantic import ValidationError

from mvir.core.models import MVIR
from mvir.extract.provider_base import ProviderError
from mvir.extract.report import FailureKind, classify_exception


def test_report_kind_provider() -> None:
    exc = ProviderError(
        provider="openai",
        kind="network",
        message="connection reset",
        retryable=True,
    )
    kind, _ = classify_exception(exc)
    assert kind == FailureKind.PROVIDER


def test_report_kind_provider_call_failure_marker() -> None:
    exc = ValueError("Provider call failed: boom")
    kind, _ = classify_exception(exc)
    assert kind == FailureKind.PROVIDER


def test_report_kind_json_parse() -> None:
    exc = ValueError("JSON parse failed: bad payload")
    kind, _ = classify_exception(exc)
    assert kind == FailureKind.JSON_PARSE


def test_report_kind_schema_validation() -> None:
    try:
        MVIR.model_validate({})
    except ValidationError as exc:
        kind, _ = classify_exception(exc)
        assert kind == FailureKind.SCHEMA_VALIDATION
    else:
        raise AssertionError("Expected ValidationError")


def test_report_kind_grounding_contract() -> None:
    exc = ValueError("Grounding contract failed: bad span")
    kind, _ = classify_exception(exc)
    assert kind == FailureKind.GROUNDING_CONTRACT


def test_report_kind_unknown() -> None:
    exc = RuntimeError("unexpected")
    kind, _ = classify_exception(exc)
    assert kind == FailureKind.UNKNOWN


def test_formalize_dir_failure_includes_debug_path(tmp_path: Path) -> None:
    input_dir = tmp_path / "problems"
    input_dir.mkdir()
    out_dir = tmp_path / "out"
    report_path = tmp_path / "report.json"
    debug_dir = tmp_path / "debug"

    (input_dir / "missing.txt").write_text("x", encoding="utf-8")
    mock_path = tmp_path / "mock.json"
    mock_path.write_text(json.dumps({}), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mvir.cli.formalize_dir",
            str(input_dir),
            "--provider",
            "mock",
            "--mock-path",
            str(mock_path),
            "--out-dir",
            str(out_dir),
            "--report",
            str(report_path),
            "--debug-dir",
            str(debug_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report["failed"]) == 1
    assert report["failed"][0]["id"] == "missing"
    assert report["failed"][0]["debug_path"] == str(debug_dir / "missing")

