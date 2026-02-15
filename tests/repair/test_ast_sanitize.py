from __future__ import annotations

from mvir.repair.ast_sanitize import sanitize_expr_dict


def test_sanitize_expr_dict_returns_none_for_broken_sum() -> None:
    expr = {"node": "Sum", "var": "k", "from": {"node": "Number", "value": 1}}
    assert sanitize_expr_dict(expr) is None


def test_sanitize_expr_dict_returns_none_for_broken_div() -> None:
    expr = {"node": "Div", "num": {"node": "Symbol", "id": "x"}}
    assert sanitize_expr_dict(expr) is None


def test_sanitize_expr_dict_returns_none_for_broken_eq() -> None:
    expr = {"node": "Eq", "lhs": {"node": "Symbol", "id": "x"}}
    assert sanitize_expr_dict(expr) is None


def test_sanitize_expr_dict_keeps_valid_pow_and_drops_null_junk() -> None:
    expr = {
        "node": "Pow",
        "base": {"node": "Symbol", "id": "x", "value": None},
        "exp": {"node": "Number", "value": 2, "id": None},
        "args": None,
    }
    assert sanitize_expr_dict(expr) == {
        "node": "Pow",
        "base": {"node": "Symbol", "id": "x"},
        "exp": {"node": "Number", "value": 2},
    }
