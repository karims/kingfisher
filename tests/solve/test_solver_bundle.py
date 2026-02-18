from __future__ import annotations

from dataclasses import asdict
import json

from mvir.core.models import MVIR
from mvir.solve.bundle import SolverBundle, build_solver_bundle


def _sample_mvir() -> MVIR:
    payload = {
        "meta": {"version": "0.1", "id": "bundle_case", "generator": "test"},
        "source": {"text": "Compute x from x+1 with x=2 and y>0."},
        "entities": [
            {"id": "x", "kind": "variable", "type": "Real", "properties": [], "trace": ["s1"]},
            {"id": "y", "kind": "variable", "type": "Integer", "properties": [], "trace": ["s1"]},
        ],
        "assumptions": [
            {
                "expr": {
                    "node": "Eq",
                    "lhs": {"node": "Symbol", "id": "x"},
                    "rhs": {"node": "Number", "value": 2},
                },
                "kind": "given",
                "trace": ["s1"],
            },
            {
                "expr": {
                    "node": "Gt",
                    "lhs": {"node": "Symbol", "id": "y"},
                    "rhs": {"node": "Number", "value": 0},
                },
                "kind": "given",
                "trace": ["s1"],
            },
            {
                "expr": {
                    "node": "Add",
                    "args": [
                        {"node": "Symbol", "id": "x"},
                        {"node": "Number", "value": 1},
                    ],
                },
                "kind": "given",
                "trace": ["s1"],
            },
        ],
        "goal": {
            "kind": "compute",
            "expr": {
                "node": "Add",
                "args": [
                    {"node": "Symbol", "id": "x"},
                    {"node": "Number", "value": 1},
                ],
            },
            "target": {"node": "Symbol", "id": "x"},
            "trace": ["s1"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [{"span_id": "s1", "start": 0, "end": 34, "text": "Compute x from x+1 with x=2 and y>0."}],
    }
    return MVIR.model_validate(payload)


def test_build_solver_bundle_fields_and_json_serializable() -> None:
    bundle = build_solver_bundle(_sample_mvir())
    payload = asdict(bundle)

    assert isinstance(bundle, SolverBundle)
    assert payload["problem_id"] == "bundle_case"
    assert payload["goal_kind"] == "compute"
    assert payload["goal_sympy"] is not None
    assert payload["constraints_sympy"] == ["Eq(x, 2)", "y > 0"]
    assert payload["unknowns"] == ["x"]
    assert payload["symbol_table"] == ["x", "y"]
    assert any("non-relational" in message for message in payload["warnings"])

    json.dumps(payload)
