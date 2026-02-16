"""Integration tests for ast_normalize + ast_contract pipeline."""

from __future__ import annotations

import pytest

from mvir.core.ast import parse_expr
from mvir.core.ast_normalize import normalize_expr_dict_with_warnings


@pytest.mark.parametrize(
    ("src", "expected_code_sequence"),
    [
        (
            {"node": "Add", "terms": [{"node": "Number", "value": 1}, {"node": "Number", "value": 2}]},
            [],
        ),
        (
            {"node": "Symbol", "name": "x"},
            [],
        ),
        (
            {
                "node": "lt",
                "lhs": {"node": "Symbol", "name": "x"},
                "rhs": {"node": "Number", "value": 0},
            },
            ["expr_normalize_repair"],
        ),
    ],
)
def test_normalized_exprs_parse_and_warning_codes_are_stable(
    src: dict, expected_code_sequence: list[str]
) -> None:
    normalized, warnings = normalize_expr_dict_with_warnings(src)
    assert normalized is not None
    _expr = parse_expr(normalized)
    codes = [w.code for w in warnings]
    assert codes == expected_code_sequence


def test_invalid_binary_missing_rhs_returns_none_with_contract_path() -> None:
    src = {"node": "Eq", "lhs": {"node": "Symbol", "name": "x"}}
    normalized, warnings = normalize_expr_dict_with_warnings(src)
    assert normalized is None
    error_warnings = [w for w in warnings if w.code == "expr_contract_error"]
    assert error_warnings
    details = error_warnings[0].details or {}
    assert details.get("path") == ("rhs",)
