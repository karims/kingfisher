"""CLI tests for golden regression runner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mvir.cli import golden as cli_golden


def _mvir_payload(problem_id: str, text: str, *, goal_value: bool = True) -> dict:
    return {
        "meta": {
            "version": "0.1",
            "id": problem_id,
            "generator": "test",
            "created_at": "2026-01-01T00:00:00Z",
        },
        "source": {"text": text},
        "entities": [],
        "assumptions": [],
        "goal": {
            "kind": "prove",
            "expr": {"node": "Bool", "value": goal_value},
            "trace": ["s0"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [{"span_id": "s0", "start": 0, "end": len(text), "text": text}],
    }


class _DummyMVIR:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def model_dump(self, by_alias: bool = False, exclude_none: bool = True) -> dict:
        _ = by_alias
        _ = exclude_none
        return self._payload


class _DummyOpenAIProvider:
    name = "openai"

    def __init__(self) -> None:
        self.top_p = None
        self.seed = None


def test_cli_golden_ignores_json_schema_and_json_object_variants(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    baseline = _mvir_payload("a", "x")
    (tmp_path / "a.json").write_text(json.dumps(baseline), encoding="utf-8")
    (tmp_path / "a.json_object.json").write_text("{}", encoding="utf-8")
    (tmp_path / "a.json_schema.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(cli_golden, "build_provider", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        cli_golden,
        "formalize_text_to_mvir",
        lambda *args, **kwargs: _DummyMVIR(_mvir_payload("a", "x")),
    )

    rc = cli_golden.main(["--input-dir", str(tmp_path), "--provider", "openai"])
    out = capsys.readouterr().out

    assert rc == 0
    assert "total=1 mismatches=0 failed=0 degraded=0" in out
    assert "a.json_object.json" not in out
    assert "a.json_schema.json" not in out


def test_cli_golden_update_overwrites_baseline_on_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    baseline_path = tmp_path / "a.json"
    baseline_path.write_text(json.dumps(_mvir_payload("a", "x", goal_value=True)), encoding="utf-8")

    monkeypatch.setattr(cli_golden, "build_provider", lambda *args, **kwargs: object())
    rerun_payload = _mvir_payload("a", "x", goal_value=False)
    monkeypatch.setattr(
        cli_golden,
        "formalize_text_to_mvir",
        lambda *args, **kwargs: _DummyMVIR(rerun_payload),
    )

    rc = cli_golden.main(
        ["--input-dir", str(tmp_path), "--provider", "openai", "--update"]
    )
    out = capsys.readouterr().out

    assert rc == 0
    assert f"UPDATE: {baseline_path}" in out
    assert "total=1 mismatches=1 failed=0 degraded=0" in out

    updated = json.loads(baseline_path.read_text(encoding="utf-8"))
    expected = cli_golden._normalize_for_compare(rerun_payload)
    assert updated == expected


def test_cli_golden_fail_on_mismatch_returns_non_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    baseline_path = tmp_path / "a.json"
    baseline_path.write_text(json.dumps(_mvir_payload("a", "x", goal_value=True)), encoding="utf-8")

    monkeypatch.setattr(cli_golden, "build_provider", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        cli_golden,
        "formalize_text_to_mvir",
        lambda *args, **kwargs: _DummyMVIR(_mvir_payload("a", "x", goal_value=False)),
    )

    rc = cli_golden.main(
        ["--input-dir", str(tmp_path), "--provider", "openai", "--fail-on-mismatch"]
    )
    out = capsys.readouterr().out

    assert rc == 1
    assert f"MISMATCH: {baseline_path}" in out


def test_cli_golden_counts_degraded_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    baseline = _mvir_payload("a", "x")
    (tmp_path / "a.json").write_text(json.dumps(baseline), encoding="utf-8")

    monkeypatch.setattr(cli_golden, "build_provider", lambda *args, **kwargs: object())
    degraded_payload = _mvir_payload("a", "x")
    degraded_payload["warnings"] = [
        {
            "code": "invalid_goal_expr_replaced",
            "message": "Replaced invalid goal expression with a safe fallback Bool(true).",
            "trace": ["s0"],
        }
    ]
    monkeypatch.setattr(
        cli_golden,
        "formalize_text_to_mvir",
        lambda *args, **kwargs: _DummyMVIR(degraded_payload),
    )

    rc = cli_golden.main(["--input-dir", str(tmp_path), "--provider", "openai"])
    out = capsys.readouterr().out

    assert rc == 0
    assert "degraded=1" in out


def test_cli_golden_passes_non_deterministic_temperature_for_openai(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    baseline = _mvir_payload("a", "x")
    (tmp_path / "a.json").write_text(json.dumps(baseline), encoding="utf-8")

    provider = _DummyOpenAIProvider()
    monkeypatch.setattr(cli_golden, "build_provider", lambda *args, **kwargs: provider)
    captured: dict = {}

    def _fake_formalize(*args, **kwargs):
        captured["temperature"] = kwargs.get("temperature")
        captured["provider_top_p"] = getattr(provider, "top_p", None)
        captured["provider_seed"] = getattr(provider, "seed", None)
        return _DummyMVIR(_mvir_payload("a", "x"))

    monkeypatch.setattr(cli_golden, "formalize_text_to_mvir", _fake_formalize)

    rc = cli_golden.main(
        ["--input-dir", str(tmp_path), "--provider", "openai", "--temperature", "0.7"]
    )
    _ = capsys.readouterr().out

    assert rc == 0
    assert captured["temperature"] == 0.7
    assert captured["provider_top_p"] == 1.0
    assert captured["provider_seed"] is None


def test_cli_golden_forces_deterministic_sampling_for_openai(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    baseline = _mvir_payload("a", "x")
    (tmp_path / "a.json").write_text(json.dumps(baseline), encoding="utf-8")

    provider = _DummyOpenAIProvider()
    monkeypatch.setattr(cli_golden, "build_provider", lambda *args, **kwargs: provider)
    captured: dict = {}

    def _fake_formalize(*args, **kwargs):
        captured["temperature"] = kwargs.get("temperature")
        captured["provider_top_p"] = getattr(provider, "top_p", None)
        return _DummyMVIR(_mvir_payload("a", "x"))

    monkeypatch.setattr(cli_golden, "formalize_text_to_mvir", _fake_formalize)

    rc = cli_golden.main(
        [
            "--input-dir",
            str(tmp_path),
            "--provider",
            "openai",
            "--temperature",
            "0.7",
            "--deterministic",
        ]
    )
    _ = capsys.readouterr().out

    assert rc == 0
    assert captured["temperature"] == 0.0
    assert captured["provider_top_p"] == 1.0
