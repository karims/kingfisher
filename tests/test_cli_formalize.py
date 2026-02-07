"""CLI tests for formalize entrypoint."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_cli_formalize_success(tmp_path: Path) -> None:
    problem_path = tmp_path / "sample.txt"
    problem_path.write_text("x", encoding="utf-8")

    response = {
        "meta": {"version": "0.1", "id": "sample", "generator": "mock"},
        "source": {"text": "x"},
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
            {"span_id": "s0", "start": 0, "end": 1, "text": "x"},
            {"span_id": "s1", "start": 0, "end": 1, "text": "x"},
        ],
    }
    mock_path = tmp_path / "mock.json"
    mock_path.write_text(json.dumps({"sample": json.dumps(response)}), encoding="utf-8")

    out_path = tmp_path / "out.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mvir.cli.formalize",
            str(problem_path),
            "--provider",
            "mock",
            "--mock-path",
            str(mock_path),
            "--out",
            str(out_path),
            "--print",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "OK: sample" in result.stdout
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["meta"]["id"] == "sample"
