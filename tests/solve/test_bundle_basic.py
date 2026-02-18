"""Basic tests for solver bundle export."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from mvir.core.models import MVIR
from mvir.solve.bundle import build_solver_bundle


def test_build_solver_bundle_has_expected_shape() -> None:
    payload = json.loads(Path("out/mvir/latex_smoke_01.json").read_text(encoding="utf-8"))
    mvir = MVIR.model_validate(payload)

    bundle = build_solver_bundle(mvir)
    bundle_payload = asdict(bundle)

    assert bundle_payload["problem_id"] == mvir.meta.id
    assert bundle_payload["goal_kind"] == mvir.goal.kind.value
    assert isinstance(bundle_payload["constraints_sympy"], list)
    assert isinstance(bundle_payload["unknowns"], list)
    assert isinstance(bundle_payload["symbol_table"], list)
    assert isinstance(bundle_payload["warnings"], list)
    json.dumps(bundle_payload)
