"""Solver-input bundle builder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from mvir.core import ast
from mvir.core.models import MVIR
from mvir.solve.sympy_bridge import expr_to_sympy

if TYPE_CHECKING:
    import sympy


@dataclass(slots=True)
class SolverBundle:
    problem_id: str
    goal_kind: str
    goal_sympy: str | None
    constraints_sympy: list[str]
    unknowns: list[str]
    symbol_table: list[str]
    warnings: list[str]


def _is_relation_expr(expr: ast.Expr) -> bool:
    return isinstance(expr, (ast.Eq, ast.Neq, ast.Lt, ast.Le, ast.Gt, ast.Ge))


def _extract_unknowns(mvir_obj: MVIR) -> list[str]:
    goal_kind = mvir_obj.goal.kind.value
    if goal_kind in {"find", "compute"} and isinstance(mvir_obj.goal.target, ast.Symbol):
        return [mvir_obj.goal.target.id]

    unknowns: list[str] = []
    seen: set[str] = set()
    for entity in mvir_obj.entities:
        if entity.kind.value != "variable":
            continue
        entity_type = entity.type.lower()
        if "integer" not in entity_type and "real" not in entity_type:
            continue
        if entity.id in seen:
            continue
        seen.add(entity.id)
        unknowns.append(entity.id)
    return unknowns


def build_solver_bundle(mvir_obj: MVIR) -> SolverBundle:
    """Build a compact, JSON-serializable solver bundle from MVIR."""

    sym_env: dict[str, sympy.Symbol] = {}
    warnings: list[str] = []

    goal_obj, goal_warnings, sym_env = expr_to_sympy(mvir_obj.goal.expr, sym_env=sym_env)
    for warning in goal_warnings:
        warnings.append(f"goal expr: {warning}")
    goal_sympy = str(goal_obj) if goal_obj is not None else None

    constraints_sympy: list[str] = []
    for idx, assumption in enumerate(mvir_obj.assumptions):
        if not _is_relation_expr(assumption.expr):
            warnings.append(
                f"assumption[{idx}] skipped: non-relational node={assumption.expr.node}"
            )
            continue

        converted, assumption_warnings, sym_env = expr_to_sympy(assumption.expr, sym_env=sym_env)
        if converted is None:
            if assumption_warnings:
                for warning in assumption_warnings:
                    warnings.append(f"assumption[{idx}] skipped: {warning}")
            else:
                warnings.append(f"assumption[{idx}] skipped: conversion failed")
            continue

        constraints_sympy.append(str(converted))
        for warning in assumption_warnings:
            warnings.append(f"assumption[{idx}] warning: {warning}")

    symbol_table = sorted(sym_env.keys())
    unknowns = _extract_unknowns(mvir_obj)

    return SolverBundle(
        problem_id=mvir_obj.meta.id,
        goal_kind=mvir_obj.goal.kind.value,
        goal_sympy=goal_sympy,
        constraints_sympy=constraints_sympy,
        unknowns=unknowns,
        symbol_table=symbol_table,
        warnings=warnings,
    )
