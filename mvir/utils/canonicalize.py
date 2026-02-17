"""Deterministic canonical ordering helpers for MVIR outputs."""

from __future__ import annotations

import json

from mvir.core.ast import (
    Add,
    Bool,
    Call,
    Div,
    Divides,
    Eq,
    Expr,
    Ge,
    Gt,
    Le,
    Lt,
    Mul,
    Neg,
    Neq,
    Number,
    Pow,
    Sum,
    Symbol,
    expr_to_dict,
)
from mvir.core.models import Assumption, Goal, MVIR


def _expr_sort_string(expr: Expr) -> str:
    return json.dumps(expr_to_dict(expr), sort_keys=True, separators=(",", ":"))


def canonicalize_expr(expr: Expr) -> Expr:
    """Return a non-mutating canonicalized expression tree."""

    if isinstance(expr, Symbol):
        return expr

    if isinstance(expr, Number):
        value = expr.value
        if isinstance(value, float) and value.is_integer():
            return Number(node="Number", value=int(value))
        return expr

    if isinstance(expr, Bool):
        return expr

    if isinstance(expr, Add):
        args = [canonicalize_expr(arg) for arg in expr.args]
        args = sorted(args, key=lambda arg: (arg.node, _expr_sort_string(arg)))
        return Add(node="Add", args=args)

    if isinstance(expr, Mul):
        args = [canonicalize_expr(arg) for arg in expr.args]
        args = sorted(args, key=lambda arg: (arg.node, _expr_sort_string(arg)))
        return Mul(node="Mul", args=args)

    if isinstance(expr, Eq):
        return Eq(node="Eq", lhs=canonicalize_expr(expr.lhs), rhs=canonicalize_expr(expr.rhs))

    if isinstance(expr, Pow):
        return Pow(node="Pow", base=canonicalize_expr(expr.base), exp=canonicalize_expr(expr.exp))

    if isinstance(expr, Neq):
        return Neq(node="Neq", lhs=canonicalize_expr(expr.lhs), rhs=canonicalize_expr(expr.rhs))

    if isinstance(expr, Lt):
        return Lt(node="Lt", lhs=canonicalize_expr(expr.lhs), rhs=canonicalize_expr(expr.rhs))

    if isinstance(expr, Le):
        return Le(node="Le", lhs=canonicalize_expr(expr.lhs), rhs=canonicalize_expr(expr.rhs))

    if isinstance(expr, Gt):
        return Gt(node="Gt", lhs=canonicalize_expr(expr.lhs), rhs=canonicalize_expr(expr.rhs))

    if isinstance(expr, Ge):
        return Ge(node="Ge", lhs=canonicalize_expr(expr.lhs), rhs=canonicalize_expr(expr.rhs))

    if isinstance(expr, Divides):
        return Divides(node="Divides", lhs=canonicalize_expr(expr.lhs), rhs=canonicalize_expr(expr.rhs))

    if isinstance(expr, Div):
        return Div(node="Div", num=canonicalize_expr(expr.num), den=canonicalize_expr(expr.den))

    if isinstance(expr, Neg):
        return Neg(node="Neg", arg=canonicalize_expr(expr.arg))

    if isinstance(expr, Sum):
        return Sum(
            node="Sum",
            var=expr.var,
            from_=canonicalize_expr(expr.from_),
            to=canonicalize_expr(expr.to),
            body=canonicalize_expr(expr.body),
        )

    if isinstance(expr, Call):
        return Call(node="Call", fn=expr.fn, args=[canonicalize_expr(arg) for arg in expr.args])

    return expr


def _assumption_sort_key(item: Assumption) -> tuple[str, str]:
    first_trace = item.trace[0] if item.trace else ""
    expr_key = _expr_sort_string(item.expr)
    return (first_trace, expr_key)


def _canonicalize_goal(goal: Goal) -> Goal:
    target = canonicalize_expr(goal.target) if goal.target is not None else None
    return goal.model_copy(
        update={
            "expr": canonicalize_expr(goal.expr),
            "target": target,
        }
    )


def canonicalize_mvir(mvir: MVIR) -> MVIR:
    """Return a new MVIR instance with deterministic list and expression ordering."""

    canonical_entities = sorted(mvir.entities, key=lambda item: item.id)

    canonical_assumptions = [
        assumption.model_copy(update={"expr": canonicalize_expr(assumption.expr)})
        for assumption in mvir.assumptions
    ]
    canonical_assumptions = sorted(canonical_assumptions, key=_assumption_sort_key)

    canonical_goal = _canonicalize_goal(mvir.goal)
    canonical_concepts = sorted(mvir.concepts, key=lambda item: item.id)
    canonical_warnings = sorted(mvir.warnings, key=lambda item: (item.code, item.message))

    return mvir.model_copy(
        update={
            "entities": canonical_entities,
            "assumptions": canonical_assumptions,
            "goal": canonical_goal,
            "concepts": canonical_concepts,
            "warnings": canonical_warnings,
        }
    )


def mvir_to_stable_json(mvir: MVIR) -> str:
    """Serialize MVIR to stable JSON (canonicalized, sorted keys, indented)."""

    canonical = canonicalize_mvir(mvir)
    payload = canonical.model_dump(by_alias=False, exclude_none=True)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
