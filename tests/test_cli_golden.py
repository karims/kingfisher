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
    assert "variant=json_object" in out
    assert "new=" in out


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


def test_cli_golden_update_does_not_overwrite_on_failure_and_writes_failed_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    baseline_path = tmp_path / "a.json"
    baseline_payload = _mvir_payload("a", "x", goal_value=True)
    baseline_path.write_text(json.dumps(baseline_payload), encoding="utf-8")

    monkeypatch.setattr(cli_golden, "build_provider", lambda *args, **kwargs: object())

    def _boom(*args, **kwargs):
        raise RuntimeError("provider failed")

    monkeypatch.setattr(cli_golden, "formalize_text_to_mvir", _boom)

    rc = cli_golden.main(["--input-dir", str(tmp_path), "--provider", "openai", "--update"])
    out = capsys.readouterr().out

    assert rc == 1
    assert "FAILED_ARTIFACT:" in out
    assert json.loads(baseline_path.read_text(encoding="utf-8")) == baseline_payload
    failed_artifact = tmp_path / ".debug" / "a.failed.json"
    assert failed_artifact.exists()


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


def test_cli_golden_normalize_for_compare_stable_ordering() -> None:
    payload = {
        "meta": {"version": "0.1", "id": "x", "generator": "g", "created_at": "2026-01-01"},
        "source": {"text": "x"},
        "entities": [
            {"id": "z", "kind": "variable", "type": "real", "trace": ["s2"], "properties": []},
            {"id": "a", "kind": "variable", "type": "real", "trace": ["s1"], "properties": []},
        ],
        "assumptions": [
            {
                "kind": "given",
                "expr": {"node": "Eq", "lhs": {"node": "Symbol", "id": "x"}, "rhs": {"node": "Number", "value": 2}},
                "trace": ["s2"],
            },
            {
                "kind": "given",
                "expr": {"node": "Eq", "lhs": {"node": "Symbol", "id": "x"}, "rhs": {"node": "Number", "value": 1}},
                "trace": ["s1"],
            },
        ],
        "goal": {"kind": "prove", "expr": {"node": "Bool", "value": True}, "trace": ["s0"]},
        "concepts": [
            {"id": "c2", "role": "pattern", "trace": ["s1"]},
            {"id": "c1", "role": "domain", "trace": ["s1"]},
        ],
        "warnings": [
            {"code": "b", "message": "m2", "trace": ["s2"]},
            {"code": "a", "message": "m1", "trace": ["s1"]},
        ],
        "trace": [
            {"span_id": "s2", "start": 10, "end": 11, "text": "x"},
            {"span_id": "s1", "start": 1, "end": 2, "text": "x"},
            {"span_id": "s0", "start": 0, "end": 1, "text": "x"},
        ],
    }

    normalized = cli_golden._normalize_for_compare(payload)

    assert "created_at" not in normalized["meta"]
    assert "generator" not in normalized["meta"]
    assert [e["id"] for e in normalized["entities"]] == ["a", "z"]
    assert normalized["assumptions"][0]["trace"] == ["s1"]
    assert [c["id"] for c in normalized["concepts"]] == ["c1", "c2"]
    assert [w["code"] for w in normalized["warnings"]] == ["a", "b"]
    assert [t["span_id"] for t in normalized["trace"]] == ["s0", "s1", "s2"]


def test_iter_baseline_paths_only_includes_root_level_real_baselines(tmp_path: Path) -> None:
    root = tmp_path / "out" / "mvir"
    root.mkdir(parents=True, exist_ok=True)

    (root / "latex_smoke_01.json").write_text("{}", encoding="utf-8")
    (root / "latex_smoke_01.json_object.json").write_text("{}", encoding="utf-8")
    (root / "latex_smoke_01.json_schema.json").write_text("{}", encoding="utf-8")

    debug_dir = root / ".debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    (debug_dir / "latex_smoke_01.failed.json").write_text("{}", encoding="utf-8")

    new_dir = root / ".new"
    new_dir.mkdir(parents=True, exist_ok=True)
    (new_dir / "latex_smoke_01.json").write_text("{}", encoding="utf-8")

    baselines = cli_golden.iter_baseline_paths(root)

    assert baselines == [root / "latex_smoke_01.json"]


def test_cli_golden_skips_invalid_baseline_and_continues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    invalid_baseline = tmp_path / "bad.json"
    invalid_baseline.write_text("{}", encoding="utf-8")

    valid_baseline = tmp_path / "ok.json"
    valid_payload = _mvir_payload("ok", "x")
    valid_baseline.write_text(json.dumps(valid_payload), encoding="utf-8")

    monkeypatch.setattr(cli_golden, "build_provider", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        cli_golden,
        "formalize_text_to_mvir",
        lambda *args, **kwargs: _DummyMVIR(_mvir_payload("ok", "x")),
    )

    rc = cli_golden.main(["--input-dir", str(tmp_path), "--provider", "openai"])
    out = capsys.readouterr().out

    assert rc == 0
    assert f"SKIP_BASELINE: {invalid_baseline} (baseline_invalid:" in out
    assert f"OK: {valid_baseline}" in out
