"""CLI preprocess tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_preprocess(tmp_path: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    input_path = tmp_path / "input.txt"
    input_path.write_text("Show that x = 2.", encoding="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "mvir.cli.preprocess", str(input_path), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_preprocess_context(tmp_path: Path) -> None:
    result = _run_preprocess(tmp_path, ["--context"])
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert "instructions" in payload
    assert "cue_candidates" in payload
    assert "math_candidates" in payload


def test_cli_preprocess_both(tmp_path: Path) -> None:
    result = _run_preprocess(tmp_path, ["--both"])
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert "preprocess" in payload
    assert "prompt_context" in payload
