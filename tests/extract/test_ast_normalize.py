"""Tests for AST normalization helpers."""

from __future__ import annotations

from mvir.core.ast_normalize import normalize_expr


def test_normalize_symbol_name_to_id() -> None:
    raw = {"node": "Symbol", "name": "x"}
    out = normalize_expr(raw)
    assert out["node"] == "Symbol"
    assert out["id"] == "x"
    assert "name" not in out


def test_normalize_comparison_args_to_lhs_rhs() -> None:
    raw = {
        "node": "Eq",
        "args": [{"node": "Symbol", "name": "x"}, {"node": "Number", "val": 1}],
    }
    out = normalize_expr(raw)
    assert out["node"] == "Eq"
    assert "args" not in out
    assert out["lhs"]["id"] == "x"
    assert out["rhs"]["value"] == 1


def test_normalize_add_lhs_rhs_to_args() -> None:
    raw = {
        "node": "Add",
        "lhs": {"node": "Number", "val": 1},
        "rhs": {"node": "Number", "val": 2},
    }
    out = normalize_expr(raw)
    assert out["node"] == "Add"
    assert "lhs" not in out
    assert "rhs" not in out
    assert isinstance(out["args"], list)
    assert out["args"][0]["value"] == 1
    assert out["args"][1]["value"] == 2


def test_normalize_pow_args_to_base_exp() -> None:
    raw = {
        "node": "Pow",
        "args": [{"node": "Symbol", "name": "x"}, {"node": "Number", "val": 2}],
    }
    out = normalize_expr(raw)
    assert out["node"] == "Pow"
    assert "args" not in out
    assert out["base"]["id"] == "x"
    assert out["exp"]["value"] == 2


def test_normalize_number_val_to_value() -> None:
    raw = {"node": "Number", "val": 3}
    out = normalize_expr(raw)
    assert out["node"] == "Number"
    assert out["value"] == 3
    assert "val" not in out

