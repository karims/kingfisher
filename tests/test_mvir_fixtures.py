"""Fixture validation tests for MVIR JSON examples."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mvir.core.models import MVIR, load_mvir


FIXTURE_DIR = Path("examples/expected")


def _collect_fixture_paths() -> list[Path]:
    return sorted(FIXTURE_DIR.glob("*.json"))


@pytest.mark.parametrize("path", _collect_fixture_paths())
def test_mvir_fixtures_round_trip(path: Path) -> None:
    mvir = load_mvir(str(path))
    payload = mvir.model_dump(by_alias=False, exclude_none=True)
    mvir_round = MVIR.model_validate(payload)

    filename = path.name
    expected_id = path.stem

    assert mvir_round.meta.version == "0.1", f"{filename}: unexpected meta.version"
    assert mvir_round.meta.id == expected_id, f"{filename}: unexpected meta.id"
    assert mvir_round.source.text, f"{filename}: source.text is empty"
    assert mvir_round.trace, f"{filename}: trace is empty"

    trace_ids = {span.span_id for span in mvir_round.trace}
    referenced = set()
    for entity in mvir_round.entities:
        referenced.update(entity.trace)
    for assumption in mvir_round.assumptions:
        referenced.update(assumption.trace)
    referenced.update(mvir_round.goal.trace)
    for concept in mvir_round.concepts:
        referenced.update(concept.trace)
    for warning in mvir_round.warnings:
        referenced.update(warning.trace)

    missing = sorted(ref_id for ref_id in referenced if ref_id not in trace_ids)
    assert not missing, f"{filename}: missing trace ids {missing}"


def test_mvir_fixtures_are_valid_json() -> None:
    for path in _collect_fixture_paths():
        payload = json.loads(path.read_text(encoding="utf-8"))
        MVIR.model_validate(payload)
