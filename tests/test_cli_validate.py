"""CLI validation tests for MVIR."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_cli_validate_ok() -> None:
    fixture = Path("examples/expected/mf2f_algebra_2rootsintpoly_am10tap11eqasqpam110.json")
    result = subprocess.run(
        [sys.executable, "-m", "mvir.cli.validate", str(fixture)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "OK" in result.stdout


def test_cli_validate_error(tmp_path: Path) -> None:
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps({"meta": {"version": "0.1"}}), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "mvir.cli.validate", str(bad_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
