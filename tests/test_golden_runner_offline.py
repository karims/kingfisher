"""Offline smoke test for golden regression runner."""

from __future__ import annotations

import os
import subprocess
import sys


def test_golden_runner_offline() -> None:
    env = os.environ.copy()
    env["MVIR_OFFLINE"] = "1"
    env.pop("OPENAI_API_KEY", None)
    result = subprocess.run(
        [sys.executable, "scripts/run_golden.py"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr

