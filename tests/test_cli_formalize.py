"""CLI tests for formalize entrypoint."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from mvir.cli import formalize as cli_formalize
from mvir.extract.provider_base import ProviderError
from mvir.extract.providers import openai_provider as openai_mod


def test_cli_formalize_success(tmp_path: Path) -> None:
    problem_path = tmp_path / "sample.txt"
    problem_path.write_text("x", encoding="utf-8")

    response = {
        "meta": {"version": "0.1", "id": "sample", "generator": "mock"},
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
            {"span_id": "s1", "start": 0, "end": 1, "text": "x"},
        ],
    }
    mock_path = tmp_path / "mock.json"
    mock_path.write_text(json.dumps({"sample": json.dumps(response)}), encoding="utf-8")

    out_path = tmp_path / "out.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mvir.cli.formalize",
            str(problem_path),
            "--provider",
            "mock",
            "--mock-path",
            str(mock_path),
            "--out",
            str(out_path),
            "--print",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "OK: sample" in result.stdout
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["meta"]["id"] == "sample"


def test_cli_formalize_openai_flags_passed_to_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem_path = tmp_path / "sample.txt"
    problem_path.write_text("x", encoding="utf-8")

    captured: dict = {}

    class _FakeProvider:
        name = "openai"

    class _DummyMVIR:
        def model_dump(self, by_alias: bool = False, exclude_none: bool = True) -> dict:
            _ = by_alias
            _ = exclude_none
            return {
                "meta": {"version": "0.1", "id": "sample", "generator": "test"},
                "source": {"text": "x"},
                "entities": [],
                "assumptions": [],
                "goal": {"kind": "prove", "expr": {"node": "Bool", "value": True}, "trace": ["s0"]},
                "concepts": [],
                "warnings": [],
                "trace": [{"span_id": "s0", "start": 0, "end": 1, "text": "x"}],
            }

    def _fake_build_provider(
        provider_name: str,
        *,
        mock_path: str | None = None,
        openai_format: str = "json_schema",
        openai_allow_fallback: bool = False,
    ):
        captured["provider_name"] = provider_name
        captured["mock_path"] = mock_path
        captured["openai_format"] = openai_format
        captured["openai_allow_fallback"] = openai_allow_fallback
        return _FakeProvider()

    monkeypatch.setattr(cli_formalize, "build_provider", _fake_build_provider)
    monkeypatch.setattr(
        cli_formalize,
        "formalize_text_to_mvir",
        lambda *args, **kwargs: _DummyMVIR(),
    )

    rc = cli_formalize.main(
        [
            str(problem_path),
            "--provider",
            "openai",
            "--openai-format",
            "json_object",
            "--openai-allow-fallback",
        ]
    )
    assert rc == 0
    assert captured["provider_name"] == "openai"
    assert captured["openai_format"] == "json_object"
    assert captured["openai_allow_fallback"] is True


def test_cli_formalize_bad_schema_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    problem_path = tmp_path / "sample.txt"
    problem_path.write_text("x", encoding="utf-8")
    monkeypatch.setattr(
        cli_formalize,
        "build_provider",
        lambda *args, **kwargs: object(),
    )

    def _raise(*args, **kwargs):
        raise ProviderError(
            provider="openai",
            kind="bad_schema",
            message="Invalid schema oneOf not permitted",
            retryable=False,
        )

    monkeypatch.setattr(cli_formalize, "formalize_text_to_mvir", _raise)
    rc = cli_formalize.main([str(problem_path), "--provider", "openai"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "OpenAI rejected the json_schema (unsupported schema feature)." in out


def test_cli_formalize_unsupported_json_schema_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    problem_path = tmp_path / "sample.txt"
    problem_path.write_text("x", encoding="utf-8")
    monkeypatch.setattr(
        cli_formalize,
        "build_provider",
        lambda *args, **kwargs: object(),
    )

    def _raise(*args, **kwargs):
        raise ProviderError(
            provider="openai",
            kind="bad_response",
            message="text.format json_schema is not supported for this model",
            retryable=False,
        )

    monkeypatch.setattr(cli_formalize, "formalize_text_to_mvir", _raise)
    rc = cli_formalize.main([str(problem_path), "--provider", "openai"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "OpenAI model does not support json_schema enforcement." in out


def test_cli_formalize_passes_temperature_zero_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem_path = tmp_path / "sample.txt"
    problem_path.write_text("x", encoding="utf-8")
    captured: dict = {}

    class _DummyMVIR:
        def model_dump(self, by_alias: bool = False, exclude_none: bool = True) -> dict:
            _ = by_alias
            _ = exclude_none
            return {
                "meta": {"version": "0.1", "id": "sample", "generator": "test"},
                "source": {"text": "x"},
                "entities": [],
                "assumptions": [],
                "goal": {"kind": "prove", "expr": {"node": "Bool", "value": True}, "trace": ["s0"]},
                "concepts": [],
                "warnings": [],
                "trace": [{"span_id": "s0", "start": 0, "end": 1, "text": "x"}],
            }

    monkeypatch.setattr(
        cli_formalize,
        "build_provider",
        lambda *args, **kwargs: object(),
    )

    def _fake_formalize_text_to_mvir(*args, **kwargs):
        captured["temperature"] = kwargs.get("temperature")
        return _DummyMVIR()

    monkeypatch.setattr(cli_formalize, "formalize_text_to_mvir", _fake_formalize_text_to_mvir)

    rc = cli_formalize.main([str(problem_path)])
    assert rc == 0
    assert captured["temperature"] == 0.0


def test_cli_formalize_openai_defaults_to_json_object_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem_path = tmp_path / "sample.txt"
    problem_path.write_text("x", encoding="utf-8")
    out_path = tmp_path / "out.json"

    class _FakeResponse:
        def __init__(self, payload: dict) -> None:
            self.status_code = 200
            self._payload = payload
            self.text = ""

        def json(self) -> dict:
            return self._payload

    seen_payloads: list[dict] = []

    def _fake_post(url: str, *, headers: dict, json: dict, timeout: float) -> _FakeResponse:
        _ = url
        _ = headers
        _ = timeout
        seen_payloads.append(dict(json))
        payload = {
            "meta": {"version": "0.1", "id": "sample", "generator": "openai-test"},
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
                {"span_id": "s1", "start": 0, "end": 1, "text": "x"},
            ],
        }
        return _FakeResponse({"output_text": json_module.dumps(payload)})

    import json as json_module

    openai_mod.OpenAIProvider._supports_json_schema.clear()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(openai_mod, "_requests_post", _fake_post)

    rc = cli_formalize.main(
        [str(problem_path), "--provider", "openai", "--out", str(out_path)]
    )
    assert rc == 0
    assert len(seen_payloads) == 1
    assert seen_payloads[0]["text"]["format"]["type"] == "json_object"
