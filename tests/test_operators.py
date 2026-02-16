"""Unit tests for operator registry lookups."""

from __future__ import annotations

from mvir.core.operators import DEFAULT_REGISTRY


def test_operator_lookup_latex_alias() -> None:
    spec = DEFAULT_REGISTRY.lookup(r"\leq")
    assert spec is not None
    assert spec.canonical_id == "le"
    assert spec.ast_node == "Le"


def test_operator_lookup_unicode_alias() -> None:
    spec = DEFAULT_REGISTRY.lookup("∩")
    assert spec is not None
    assert spec.canonical_id == "set_intersection"
    assert spec.ast_node == "Call"
    assert spec.emit_call_fn == "intersection"


def test_operator_lookup_word_alias() -> None:
    spec = DEFAULT_REGISTRY.lookup("integral")
    assert spec is not None
    assert spec.canonical_id == "integral"
    assert spec.ast_node == "Call"
    assert spec.emit_call_fn == "integral"


def test_operator_canonical_lookup() -> None:
    add_spec = DEFAULT_REGISTRY.canonical("Add")
    sum_spec = DEFAULT_REGISTRY.canonical("Sum")
    assert add_spec is not None
    assert add_spec.canonical_id == "add"
    assert sum_spec is not None
    assert sum_spec.canonical_id == "sum"


def test_operator_all_nodes_contains_required_ast_nodes() -> None:
    nodes = DEFAULT_REGISTRY.all_nodes()
    assert {
        "Add",
        "Mul",
        "Div",
        "Pow",
        "Neg",
        "Eq",
        "Neq",
        "Lt",
        "Le",
        "Gt",
        "Ge",
        "Divides",
        "Sum",
        "Call",
    }.issubset(nodes)
