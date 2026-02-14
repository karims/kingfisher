"""Offline CLI tests for formalize_dir with openai provider."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def test_cli_formalize_dir_openai_offline(tmp_path: Path) -> None:
    input_dir = tmp_path / "problems"
    input_dir.mkdir()
    out_dir = tmp_path / "out"
    report_path = tmp_path / "report.json"

    shutil.copy2(
        "examples/problems/mf2f_amc12a_2015_p10.txt",
        input_dir / "mf2f_amc12a_2015_p10.txt",
    )
    shutil.copy2(
        "examples/problems/mf2f_algebra_2rootsintpoly_am10tap11eqasqpam110.txt",
        input_dir / "mf2f_algebra_2rootsintpoly_am10tap11eqasqpam110.txt",
    )

    sitecustomize_path = tmp_path / "sitecustomize.py"
    sitecustomize_path.write_text(
        "\n".join(
            [
                "import json",
                "import re",
                "from mvir.extract.providers.openai_provider import OpenAIProvider",
                "",
                "def _fake_complete(self, prompt, *, temperature=0.0, max_tokens=2000):",
                "    _ = temperature",
                "    _ = max_tokens",
                "    problem_id = 'unknown'",
                "    for line in prompt.splitlines():",
                "        if line.startswith('PROBLEM_ID='):",
                "            problem_id = line.split('=', 1)[1].strip()",
                "            break",
                "    marker = 'PROMPT_CONTEXT_JSON:\\n'",
                "    text = ''",
                "    if marker in prompt:",
                "        raw = prompt.split(marker, 1)[1]",
                "        ctx = json.loads(raw)",
                "        text = ctx.get('source_text', '')",
                "    regex = re.compile(r'[^.!?]+[.!?]?')",
                "    trace = [{'span_id': 's0', 'start': 0, 'end': len(text), 'text': text}]",
                "    idx = 1",
                "    for m in regex.finditer(text):",
                "        snippet = m.group(0)",
                "        if snippet.strip():",
                "            trace.append({",
                "                'span_id': f's{idx}',",
                "                'start': m.start(),",
                "                'end': m.end(),",
                "                'text': snippet,",
                "            })",
                "            idx += 1",
                "    if len(trace) < 2:",
                "        trace.append({'span_id': 's1', 'start': 0, 'end': len(text), 'text': text})",
                "    payload = {",
                "        'meta': {'version': '0.1', 'id': problem_id, 'generator': 'offline-openai'},",
                "        'source': {'text': text},",
                "        'entities': [],",
                "        'assumptions': [],",
                "        'goal': {",
                "            'kind': 'prove',",
                "            'expr': {'node': 'Bool', 'value': True},",
                "            'trace': ['s0'],",
                "        },",
                "        'concepts': [],",
                "        'warnings': [],",
                "        'trace': trace,",
                "    }",
                "    return json.dumps(payload)",
                "",
                "OpenAIProvider.complete = _fake_complete",
            ]
        ),
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["OPENAI_API_KEY"] = "test-key"
    env["PYTHONPATH"] = str(tmp_path) + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mvir.cli.formalize_dir",
            str(input_dir),
            "--provider",
            "openai",
            "--out-dir",
            str(out_dir),
            "--report",
            str(report_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0
    assert "total=2 ok=2 failed=0" in result.stdout
    assert (out_dir / "mf2f_amc12a_2015_p10.json").exists()
    assert (out_dir / "mf2f_algebra_2rootsintpoly_am10tap11eqasqpam110.json").exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert sorted(report["ok"]) == [
        "mf2f_algebra_2rootsintpoly_am10tap11eqasqpam110",
        "mf2f_amc12a_2015_p10",
    ]
    assert report["failed"] == []

