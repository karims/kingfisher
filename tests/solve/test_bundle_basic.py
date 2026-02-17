"""Basic tests for solver bundle export."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from mvir.solve.bundle import build_solver_bundle


def test_build_solver_bundle_has_expected_shape_and_sorted_entities() -> None:
    payload = json.loads(Path("out/mvir/latex_smoke_01.json").read_text(encoding="utf-8"))

    bundle = build_solver_bundle(payload)

    assert "entities" in bundle
    assert "goal" in bundle
    assert "assumptions" in bundle

    entity_ids = [item["id"] for item in bundle["entities"]]
    assert entity_ids == sorted(entity_ids)

    assert bundle["goal"]["expr_mvir"]
    assert isinstance(bundle["assumptions"], list)

    sympy_available = importlib.util.find_spec("sympy") is not None
    if sympy_available:
        assert bundle["goal"]["expr_sympy"] is not None
    else:
        assert bundle["goal"]["expr_sympy"] is None

