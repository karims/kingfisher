"""Unit tests for MVIR AST normalizer."""

from __future__ import annotations

from mvir.core.ast_normalize import normalize_expr_dict


def test_symbol_name_to_id() -> None:
    src = {"node": "Symbol", "name": "x", "extra": 1}
    out = normalize_expr_dict(src)
    assert out == {"node": "Symbol", "id": "x"}


def test_gt_args_to_lhs_rhs() -> None:
    src = {
        "node": "Gt",
        "args": [{"node": "Symbol", "name": "x"}, {"node": "Number", "val": "0"}],
        "noise": True,
    }
    out = normalize_expr_dict(src)
    assert out["node"] == "Gt"
    assert "args" not in out
    assert set(out.keys()) == {"node", "lhs", "rhs"}
    assert out["lhs"] == {"node": "Symbol", "id": "x"}
    assert out["rhs"] == {"node": "Number", "value": 0}


def test_pow_args_to_base_exp() -> None:
    src = {
        "node": "Pow",
        "args": [{"node": "Symbol", "name": "x"}, {"node": "Number", "val": 2}],
        "other": "drop",
    }
    out = normalize_expr_dict(src)
    assert out["node"] == "Pow"
    assert "args" not in out
    assert set(out.keys()) == {"node", "base", "exp"}
    assert out["base"] == {"node": "Symbol", "id": "x"}
    assert out["exp"] == {"node": "Number", "value": 2}


def test_add_flattening() -> None:
    src = {
        "node": "Add",
        "args": [
            {
                "node": "Add",
                "args": [{"node": "Number", "value": 1}, {"node": "Number", "value": 2}],
            },
            {"node": "Number", "value": 3},
        ],
        "junk": "x",
    }
    out = normalize_expr_dict(src)
    assert out["node"] == "Add"
    assert set(out.keys()) == {"node", "args"}
    assert out["args"] == [
        {"node": "Number", "value": 1},
        {"node": "Number", "value": 2},
        {"node": "Number", "value": 3},
    ]


def test_bool_true_false_coercion() -> None:
    true_out = normalize_expr_dict({"node": "True", "anything": 1})
    false_out = normalize_expr_dict({"node": "False"})
    assert true_out == {"node": "Bool", "value": True}
    assert false_out == {"node": "Bool", "value": False}


def test_stray_fields_removed() -> None:
    src = {
        "node": "Eq",
        "lhs": {"node": "Symbol", "id": "a", "z": 1},
        "rhs": {"node": "Number", "value": "2"},
        "ignored": "drop",
    }
    out = normalize_expr_dict(src)
    assert set(out.keys()) == {"node", "lhs", "rhs"}
    assert out["lhs"] == {"node": "Symbol", "id": "a"}
    assert out["rhs"] == {"node": "Number", "value": 2}

