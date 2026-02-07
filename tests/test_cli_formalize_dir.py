"""CLI tests for directory formalization."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _mvir_payload(problem_id: str, text: str) -> dict:
    return {
        "meta": {"version": "0.1", "id": problem_id, "generator": "mock"},
        "source": {"text": text},
        "entities": [],
        "assumptions": [],
        "goal": {
            "kind": "prove",
            "expr": {"node": "Bool", "value": True},
            "trace": ["s0"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": len(text), "text": text},
            {"span_id": "s1", "start": 0, "end": len(text), "text": text},
        ],
    }


def test_cli_formalize_dir_success_and_report(tmp_path: Path) -> None:
    input_dir = tmp_path / "problems"
    input_dir.mkdir()
    out_dir = tmp_path / "out"
    report_path = tmp_path / "report.json"

    (input_dir / "a.txt").write_text("x", encoding="utf-8")
    (input_dir / "b.txt").write_text("y", encoding="utf-8")

    mapping = {
        "a": json.dumps(_mvir_payload("a", "x")),
        "b": json.dumps(_mvir_payload("b", "y")),
    }
    mock_path = tmp_path / "mock.json"
    mock_path.write_text(json.dumps(mapping), encoding="utf-8")

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
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert (out_dir / "a.json").exists()
    assert (out_dir / "b.json").exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert sorted(report["ok"]) == ["a", "b"]
    assert report["failed"] == []


def test_cli_formalize_dir_continues_on_failure(tmp_path: Path) -> None:
    input_dir = tmp_path / "problems"
    input_dir.mkdir()
    out_dir = tmp_path / "out"
    report_path = tmp_path / "report.json"

    (input_dir / "ok1.txt").write_text("x", encoding="utf-8")
    (input_dir / "missing.txt").write_text("z", encoding="utf-8")
    (input_dir / "ok2.txt").write_text("y", encoding="utf-8")

    mapping = {
        "ok1": json.dumps(_mvir_payload("ok1", "x")),
        "ok2": json.dumps(_mvir_payload("ok2", "y")),
    }
    mock_path = tmp_path / "mock.json"
    mock_path.write_text(json.dumps(mapping), encoding="utf-8")

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
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert (out_dir / "ok1.json").exists()
    assert (out_dir / "ok2.json").exists()
    assert not (out_dir / "missing.json").exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert sorted(report["ok"]) == ["ok1", "ok2"]
    assert len(report["failed"]) == 1
    assert report["failed"][0]["id"] == "missing"
    assert report["failed"][0]["kind"] == "provider"
    assert "Unknown PROBLEM_ID" in report["failed"][0]["message"]


def test_cli_formalize_dir_fail_fast_returns_non_zero(tmp_path: Path) -> None:
    input_dir = tmp_path / "problems"
    input_dir.mkdir()
    out_dir = tmp_path / "out"

    (input_dir / "missing.txt").write_text("z", encoding="utf-8")
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
            "--fail-fast",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
