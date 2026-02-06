"""Tests for MVIR AST parsing and validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mvir.core.ast import expr_to_dict, parse_expr


def _round_trip(payload: dict) -> None:
    expr = parse_expr(payload)
    assert expr_to_dict(expr) == payload


def test_round_trip_all_nodes() -> None:
    cases = [
        {"node": "Symbol", "id": "x"},
        {"node": "Number", "value": 3},
        {"node": "Number", "value": 2.5},
        {"node": "Bool", "value": True},
        {"node": "Add", "args": [{"node": "Number", "value": 1}]},
        {"node": "Mul", "args": [{"node": "Number", "value": 2}]},
        {
            "node": "Div",
            "num": {"node": "Symbol", "id": "a"},
            "den": {"node": "Symbol", "id": "b"},
        },
        {
            "node": "Pow",
            "base": {"node": "Symbol", "id": "x"},
            "exp": {"node": "Number", "value": 2},
        },
        {"node": "Neg", "arg": {"node": "Symbol", "id": "x"}},
        {
            "node": "Eq",
            "lhs": {"node": "Symbol", "id": "x"},
            "rhs": {"node": "Number", "value": 1},
        },
        {
            "node": "Neq",
            "lhs": {"node": "Symbol", "id": "x"},
            "rhs": {"node": "Number", "value": 1},
        },
        {
            "node": "Lt",
            "lhs": {"node": "Symbol", "id": "x"},
            "rhs": {"node": "Number", "value": 1},
        },
        {
            "node": "Le",
            "lhs": {"node": "Symbol", "id": "x"},
            "rhs": {"node": "Number", "value": 1},
        },
        {
            "node": "Gt",
            "lhs": {"node": "Symbol", "id": "x"},
            "rhs": {"node": "Number", "value": 1},
        },
        {
            "node": "Ge",
            "lhs": {"node": "Symbol", "id": "x"},
            "rhs": {"node": "Number", "value": 1},
        },
        {"node": "Call", "fn": "f", "args": [{"node": "Symbol", "id": "x"}]},
    ]
    for payload in cases:
        _round_trip(payload)


def test_nested_expression() -> None:
    payload = {
        "node": "Ge",
        "lhs": {
            "node": "Add",
            "args": [
                {"node": "Symbol", "id": "x"},
                {
                    "node": "Div",
                    "num": {"node": "Number", "value": 1},
                    "den": {"node": "Symbol", "id": "x"},
                },
            ],
        },
        "rhs": {"node": "Number", "value": 2},
    }
    _round_trip(payload)


def test_bool_placeholder_goal_expr() -> None:
    _round_trip({"node": "Bool", "value": False})


def test_validation_errors() -> None:
    with pytest.raises(ValidationError):
        parse_expr({"node": "Add", "args": []})
    with pytest.raises(ValidationError):
        parse_expr({"node": "Symbol", "id": ""})
    with pytest.raises(ValidationError):
        parse_expr({"node": "Call", "fn": "", "args": []})
