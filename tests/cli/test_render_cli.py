from __future__ import annotations

import json
from pathlib import Path

from mvir.cli import render as cli_render


def _minimal_mvir_payload(doc_id: str = "render_case") -> dict:
    return {
        "meta": {"version": "0.1", "id": doc_id, "generator": "test"},
        "source": {"text": "Let x > 0. Show x^2 >= 0."},
        "entities": [
            {
                "id": "x",
                "kind": "variable",
                "type": "real",
                "properties": [],
                "trace": ["s1"],
            }
        ],
        "assumptions": [
            {
                "expr": {
                    "node": "Gt",
                    "lhs": {"node": "Symbol", "id": "x"},
                    "rhs": {"node": "Number", "value": 0},
                },
                "kind": "given",
                "trace": ["s1"],
            }
        ],
        "goal": {
            "kind": "prove",
            "expr": {
                "node": "Ge",
                "lhs": {
                    "node": "Pow",
                    "base": {"node": "Symbol", "id": "x"},
                    "exp": {"node": "Number", "value": 2},
                },
                "rhs": {"node": "Number", "value": 0},
            },
            "trace": ["s2"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 25, "text": "Let x > 0. Show x^2 >= 0."},
            {"span_id": "s1", "start": 0, "end": 9, "text": "Let x > 0."},
            {"span_id": "s2", "start": 10, "end": 25, "text": "Show x^2 >= 0."},
        ],
    }


def test_cli_render_writes_default_output_path(
    tmp_path: Path, capsys
) -> None:
    input_path = tmp_path / "sample.json"
    payload = _minimal_mvir_payload("sample")
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    rc = cli_render.main([str(input_path)])
    out = capsys.readouterr().out

    expected_out = Path(str(input_path) + ".md")
    assert rc == 0
    assert expected_out.exists()
    rendered = expected_out.read_text(encoding="utf-8")
    assert "# MVIR Report: sample" in rendered
    assert f"OK: sample -> {expected_out}" in out


def test_cli_render_writes_custom_output_path(
    tmp_path: Path, capsys
) -> None:
    input_path = tmp_path / "win_path_case.json"
    payload = _minimal_mvir_payload("win_path_case")
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    out_path = tmp_path / "reports" / "rendered.md"
    rc = cli_render.main([str(input_path), "--out", str(out_path)])
    out = capsys.readouterr().out

    assert rc == 0
    assert out_path.exists()
    rendered = out_path.read_text(encoding="utf-8")
    assert "## Goal" in rendered
    assert f"OK: win_path_case -> {out_path}" in out
