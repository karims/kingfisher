from __future__ import annotations

from pathlib import Path

import pytest

from mvir.cli import formalize as cli_formalize
from mvir.core.models import MVIR


def _minimal_mvir(problem_id: str) -> MVIR:
    payload = {
        "meta": {"version": "0.1", "id": problem_id, "generator": "test"},
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
        ],
    }
    return MVIR.model_validate(payload)


def test_default_md_out_path_uses_json_out_suffix() -> None:
    out = cli_formalize._default_md_out_path("out\\sample.json")
    assert out == Path("out/sample.md")


def test_resolve_md_out_requires_out_or_md_out() -> None:
    with pytest.raises(ValueError, match="--render-md requires --out"):
        cli_formalize._resolve_md_out_path(render_md=True, json_out=None, md_out=None)


def test_write_markdown_report_from_mvir(tmp_path: Path) -> None:
    mvir = _minimal_mvir("render_unit")
    md_path = tmp_path / "report.md"

    cli_formalize._write_markdown_report(mvir, md_path)

    assert md_path.exists()
    text = md_path.read_text(encoding="utf-8")
    assert "# MVIR Report: render_unit" in text


def test_cli_formalize_render_md_writes_default_md_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem_path = tmp_path / "sample.txt"
    problem_path.write_text("x", encoding="utf-8")
    out_path = tmp_path / "out.json"

    monkeypatch.setattr(cli_formalize, "build_provider", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        cli_formalize,
        "formalize_text_to_mvir",
        lambda *args, **kwargs: _minimal_mvir("sample"),
    )

    rc = cli_formalize.main(
        [
            str(problem_path),
            "--out",
            str(out_path),
            "--render-md",
        ]
    )

    assert rc == 0
    assert out_path.exists()
    md_path = out_path.with_suffix(".md")
    assert md_path.exists()
    assert "# MVIR Report: sample" in md_path.read_text(encoding="utf-8")


def test_cli_formalize_without_render_md_does_not_write_md(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem_path = tmp_path / "sample.txt"
    problem_path.write_text("x", encoding="utf-8")
    out_path = tmp_path / "out.json"

    monkeypatch.setattr(cli_formalize, "build_provider", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        cli_formalize,
        "formalize_text_to_mvir",
        lambda *args, **kwargs: _minimal_mvir("sample"),
    )

    rc = cli_formalize.main([str(problem_path), "--out", str(out_path)])

    assert rc == 0
    assert out_path.exists()
    assert not out_path.with_suffix(".md").exists()
