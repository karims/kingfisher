from __future__ import annotations

import pytest

sympy = pytest.importorskip("sympy")

from mvir.solve.verify import try_evaluate, verify_constraints


def test_verify_constraints_pass_and_fail() -> None:
    symbols = {"x": sympy.Symbol("x")}
    constraints = ["x>0", "Eq(x**2,4)"]

    ok_pass, failed_pass = verify_constraints(constraints, symbols, {"x": 2})
    ok_fail, failed_fail = verify_constraints(constraints, symbols, {"x": -2})

    assert ok_pass is True
    assert failed_pass == []
    assert ok_fail is False
    assert "x>0" in failed_fail


def test_verify_constraints_parse_error_is_reported() -> None:
    symbols = {"x": sympy.Symbol("x")}
    ok, failed = verify_constraints(["Eq(x**,4)"], symbols, {"x": 2})

    assert ok is False
    assert len(failed) == 1
    assert "parse_error" in failed[0]


def test_try_evaluate_returns_value_or_reason() -> None:
    symbols = {"x": sympy.Symbol("x")}

    value, error = try_evaluate("x+1", symbols, {"x": 2})
    bad_value, bad_error = try_evaluate("Eq(x,2)", symbols, {"x": 2})

    assert value == 3.0
    assert error is None
    assert bad_value is None
    assert bad_error is not None
