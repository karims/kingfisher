from __future__ import annotations

import json
from pathlib import Path

from mvir.core.models import MVIR
from mvir.render.bundle import write_explain_bundle


def _sample_mvir(doc_id: str = "bundle_case") -> MVIR:
    payload = {
        "meta": {"version": "0.1", "id": doc_id, "generator": "test"},
        "source": {"text": "Let x > 0. Show x^2 >= 0."},
        "entities": [
            {"id": "x", "kind": "variable", "type": "real", "properties": [], "trace": ["s1"]}
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
            {"span_id": "s0", "start": 0, "end": 25, "text": "Let x > 0.\nShow x^2 >= 0."},
            {"span_id": "s1", "start": 0, "end": 9, "text": "Let x > 0."},
            {"span_id": "s2", "start": 10, "end": 25, "text": "Show x^2 >= 0."},
        ],
    }
    return MVIR.model_validate(payload)


def test_write_explain_bundle_writes_expected_files(tmp_path: Path) -> None:
    mvir = _sample_mvir()
    out_dir = tmp_path / "bundles" / mvir.meta.id

    write_explain_bundle(mvir, out_dir)

    json_path = out_dir / "mvir.json"
    md_path = out_dir / "mvir.md"
    trace_path = out_dir / "trace.txt"

    assert json_path.exists()
    assert md_path.exists()
    assert trace_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload == mvir.model_dump(by_alias=False, exclude_none=True)
    assert "# MVIR Report: bundle_case" in md_path.read_text(encoding="utf-8")


def test_write_explain_bundle_trace_txt_format_is_deterministic(tmp_path: Path) -> None:
    mvir = _sample_mvir()
    out_dir = tmp_path / "bundle"

    write_explain_bundle(mvir, out_dir)

    lines = (out_dir / "trace.txt").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "s0\t0\t25\tLet x > 0.\\nShow x^2 >= 0."
    assert lines[1] == "s1\t0\t9\tLet x > 0."
    assert lines[2] == "s2\t10\t25\tShow x^2 >= 0."


def test_write_explain_bundle_is_stable_across_rewrites(tmp_path: Path) -> None:
    mvir = _sample_mvir("stable_case")
    out_dir = tmp_path / "bundle"

    write_explain_bundle(mvir, out_dir)
    first_json = (out_dir / "mvir.json").read_text(encoding="utf-8")
    first_md = (out_dir / "mvir.md").read_text(encoding="utf-8")
    first_trace = (out_dir / "trace.txt").read_text(encoding="utf-8")

    write_explain_bundle(mvir, out_dir)

    assert (out_dir / "mvir.json").read_text(encoding="utf-8") == first_json
    assert (out_dir / "mvir.md").read_text(encoding="utf-8") == first_md
    assert (out_dir / "trace.txt").read_text(encoding="utf-8") == first_trace
