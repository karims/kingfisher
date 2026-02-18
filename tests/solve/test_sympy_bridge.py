"""Unit tests for MVIR -> SymPy bridge."""

from __future__ import annotations

import pytest

sympy = pytest.importorskip("sympy")

from mvir.core import ast
from mvir.solve.sympy_bridge import expr_to_sympy


def test_expr_to_sympy_pow_add() -> None:
    expr = ast.Add(
        node="Add",
        args=[
            ast.Pow(
                node="Pow",
                base=ast.Symbol(node="Symbol", id="x"),
                exp=ast.Number(node="Number", value=2),
            ),
            ast.Number(node="Number", value=1),
        ],
    )

    out, warnings, env = expr_to_sympy(expr)

    x = sympy.Symbol("x")
    assert out == x**2 + 1
    assert warnings == []
    assert env["x"] == x


def test_expr_to_sympy_sum() -> None:
    expr = ast.Sum(
        node="Sum",
        var="k",
        **{"from": ast.Number(node="Number", value=1)},
        to=ast.Symbol(node="Symbol", id="n"),
        body=ast.Symbol(node="Symbol", id="k"),
    )

    out, warnings, env = expr_to_sympy(expr)

    k = sympy.Symbol("k")
    n = sympy.Symbol("n")
    assert out == sympy.Sum(k, (k, 1, n))
    assert warnings == []
    assert env["k"] == k
    assert env["n"] == n


def test_expr_to_sympy_relations() -> None:
    eq_expr = ast.Eq(
        node="Eq",
        lhs=ast.Symbol(node="Symbol", id="x"),
        rhs=ast.Number(node="Number", value=1),
    )
    ge_expr = ast.Ge(
        node="Ge",
        lhs=ast.Symbol(node="Symbol", id="x"),
        rhs=ast.Number(node="Number", value=0),
    )

    eq_out, eq_warnings, _ = expr_to_sympy(eq_expr)
    ge_out, ge_warnings, _ = expr_to_sympy(ge_expr)

    x = sympy.Symbol("x")
    assert eq_out == sympy.Eq(x, 1)
    assert ge_out == sympy.Ge(x, 0)
    assert eq_warnings == []
    assert ge_warnings == []


def test_expr_to_sympy_unsupported_call_warns() -> None:
    expr = ast.Call(
        node="Call",
        fn="foo",
        args=[ast.Symbol(node="Symbol", id="x")],
    )

    out, warnings, env = expr_to_sympy(expr)

    assert out is None
    assert "unsupported Call fn=foo" in warnings
    assert env == {}
