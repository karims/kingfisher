from __future__ import annotations

import json
from pathlib import Path

from mvir.cli import formalize as cli_formalize


def test_cli_formalize_writes_surface_and_bundle_artifacts(tmp_path: Path) -> None:
    problem_path = tmp_path / "sample.txt"
    problem_path.write_text("Compute $x+1$.", encoding="utf-8")

    response = {
        "meta": {"version": "0.1", "id": "sample", "generator": "mock"},
        "source": {"text": "Compute $x+1$."},
        "entities": [{"id": "x", "kind": "variable", "type": "Real", "properties": [], "trace": ["s1"]}],
        "assumptions": [],
        "goal": {
            "kind": "compute",
            "expr": {"node": "Add", "args": [{"node": "Symbol", "id": "x"}, {"node": "Number", "value": 1}]},
            "trace": ["s1"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 14, "text": "Compute $x+1$."},
            {"span_id": "s1", "start": 0, "end": 14, "text": "Compute $x+1$."},
        ],
    }
    mock_path = tmp_path / "mock.json"
    mock_path.write_text(json.dumps({"sample": json.dumps(response)}), encoding="utf-8")

    out_path = tmp_path / "out.json"
    surface_path = tmp_path / "surface.json"
    bundle_path = tmp_path / "bundle.json"
    rc = cli_formalize.main(
        [
            str(problem_path),
            "--provider",
            "mock",
            "--mock-path",
            str(mock_path),
            "--out",
            str(out_path),
            "--surface-out",
            str(surface_path),
            "--bundle-out",
            str(bundle_path),
        ]
    )

    assert rc == 0
    assert out_path.exists()
    assert surface_path.exists()
    assert bundle_path.exists()

    surface_payload = json.loads(surface_path.read_text(encoding="utf-8"))
    bundle_payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert isinstance(surface_payload, list)
    assert "problem_id" in bundle_payload
    assert "goal_kind" in bundle_payload
    assert "goal_sympy" in bundle_payload
    assert "constraints_sympy" in bundle_payload
