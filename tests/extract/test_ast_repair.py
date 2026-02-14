"""Tests for AST repair using span text context."""

from __future__ import annotations

from mvir.core.models import Entity, EntityKind
from mvir.extract.ast_repair import repair_expr


def test_repair_gt_partial_expr_from_span_text() -> None:
    expr = {
        "node": "Gt",
        "lhs": {"node": "Symbol"},
        "rhs": {"node": "Number"},
    }
    entities = [Entity(id="x", kind=EntityKind.VARIABLE, type="real")]

    repaired = repair_expr(expr, span_text="Let (x > 0).", entities=entities)

    assert repaired["node"] == "Gt"
    assert repaired["lhs"]["node"] == "Symbol"
    assert repaired["lhs"]["id"] == "x"
    assert repaired["rhs"]["node"] == "Number"
    assert repaired["rhs"]["value"] == 0


def test_repair_ge_pow_partial_expr_from_span_text() -> None:
    expr = {
        "node": "Ge",
        "lhs": {"node": "Pow"},
        "rhs": {"node": "Number"},
    }
    entities = [Entity(id="x", kind=EntityKind.VARIABLE, type="real")]

    repaired = repair_expr(expr, span_text="Show that [x^2 >= 0].", entities=entities)

    assert repaired["node"] == "Ge"
    assert repaired["lhs"]["node"] == "Pow"
    assert repaired["lhs"]["base"]["node"] == "Symbol"
    assert repaired["lhs"]["base"]["id"] == "x"
    assert repaired["lhs"]["exp"]["node"] == "Number"
    assert repaired["lhs"]["exp"]["value"] == 2
    assert repaired["rhs"]["node"] == "Number"
    assert repaired["rhs"]["value"] == 0

