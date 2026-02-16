"""Unit tests for internal AST contract validator."""

from __future__ import annotations

import pytest

from mvir.core.ast_contract import validate_expr_dict


@pytest.mark.parametrize(
    ("src", "expected", "repair_tag"),
    [
        (
            {"node": "Add", "terms": [{"node": "Number", "value": 1}, {"node": "Number", "value": 2}]},
            {"node": "Add", "args": [{"node": "Number", "value": 1}, {"node": "Number", "value": 2}]},
            "add_terms_to_args",
        ),
        (
            {"node": "Symbol", "name": "x"},
            {"node": "Symbol", "id": "x"},
            "symbol_name_to_id",
        ),
        (
            {
                "node": "Sum",
                "var": "k",
                "from_": {"node": "Number", "value": 1},
                "to": {"node": "Number", "value": 3},
                "body": {"node": "Symbol", "id": "k"},
            },
            {
                "node": "Sum",
                "var": "k",
                "from": {"node": "Number", "value": 1},
                "to": {"node": "Number", "value": 3},
                "body": {"node": "Symbol", "id": "k"},
            },
            "sum_from_alias_to_from",
        ),
    ],
)
def test_validate_expr_dict_repairs_common_shapes(src: dict, expected: dict, repair_tag: str) -> None:
    repaired, warnings = validate_expr_dict(src, allow_repair=True)
    assert repaired == expected
    assert any(w.code == "expr_contract_repair" for w in warnings)
    assert any((w.details or {}).get("repair") == repair_tag for w in warnings)
    assert not any(w.code == "expr_contract_error" for w in warnings)


@pytest.mark.parametrize(
    ("src", "expected_path"),
    [
        ({"node": "Eq", "lhs": {"node": "Symbol", "id": "x"}}, ("rhs",)),
        (
            {"node": "Sum", "var": "k", "from": {"node": "Number", "value": 1}},
            ("to",),
        ),
        ({"node": "Symbol"}, ("id",)),
        ({"node": "Add"}, ("args",)),
    ],
)
def test_validate_expr_dict_reports_contract_errors_with_pydantic_like_paths(
    src: dict, expected_path: tuple
) -> None:
    _repaired, warnings = validate_expr_dict(src, allow_repair=True)
    errors = [w for w in warnings if w.code == "expr_contract_error"]
    assert errors
    assert any((w.details or {}).get("path") == expected_path for w in errors)


def test_validate_expr_dict_allow_repair_false_keeps_missing_symbol_id_as_error() -> None:
    repaired, warnings = validate_expr_dict({"node": "Symbol", "name": "x"}, allow_repair=False)
    assert repaired == {}
    errors = [w for w in warnings if w.code == "expr_contract_error"]
    assert errors
    assert errors[0].details is not None
    assert errors[0].details.get("path") == ("id",)
