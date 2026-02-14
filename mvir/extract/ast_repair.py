"""Deterministic AST repair helpers using span text context."""

from __future__ import annotations

import re
from copy import deepcopy

from mvir.core.models import Entity


_PAT_GT_ZERO = re.compile(r"([a-zA-Z])\s*>\s*0")
_PAT_GE_POW_ZERO = re.compile(r"([a-zA-Z])\s*\^\s*(\d+)\s*(?:>=|\\ge|≥)\s*0")


def repair_expr(expr: dict, *, span_text: str, entities: list[Entity]) -> dict:
    """Repair partial Expr dicts for simple Gt/Ge patterns."""

    if not isinstance(expr, dict):
        return expr

    out = deepcopy(expr)
    node = out.get("node")
    text = span_text or ""

    gt_match = _PAT_GT_ZERO.search(text)
    ge_pow_match = _PAT_GE_POW_ZERO.search(text)

    if node == "Gt":
        var_hint = gt_match.group(1) if gt_match else None
        out["lhs"] = _repair_symbol_like(out.get("lhs"), var_hint, entities)
        out["rhs"] = _repair_number_like(out.get("rhs"), 0 if gt_match else None, text)

    if node == "Ge":
        var_hint = ge_pow_match.group(1) if ge_pow_match else None
        exp_hint = int(ge_pow_match.group(2)) if ge_pow_match else None
        out["lhs"] = _repair_pow_like(out.get("lhs"), var_hint, exp_hint, entities, text)
        out["rhs"] = _repair_number_like(out.get("rhs"), 0 if ge_pow_match else None, text)

    return out


def _repair_symbol_like(value, var_hint: str | None, entities: list[Entity]) -> dict:
    out = value if isinstance(value, dict) else {"node": "Symbol"}
    if out.get("node") != "Symbol":
        return out
    symbol_id = out.get("id")
    if isinstance(symbol_id, str) and symbol_id:
        return out
    inferred = var_hint or _first_entity_id(entities)
    if inferred:
        out["id"] = inferred
    return out


def _repair_number_like(value, number_hint: int | float | None, span_text: str) -> dict:
    out = value if isinstance(value, dict) else {"node": "Number"}
    if out.get("node") != "Number":
        return out
    number_value = out.get("value")
    if isinstance(number_value, (int, float)) and not isinstance(number_value, bool):
        return out
    if number_hint is not None:
        out["value"] = number_hint
    elif "0" in span_text:
        out["value"] = 0
    return out


def _repair_pow_like(
    value,
    var_hint: str | None,
    exp_hint: int | None,
    entities: list[Entity],
    span_text: str,
) -> dict:
    out = value if isinstance(value, dict) else {"node": "Pow"}
    if out.get("node") != "Pow":
        return out

    out["base"] = _repair_symbol_like(out.get("base"), var_hint, entities)
    out["exp"] = _repair_number_like(out.get("exp"), exp_hint, span_text)
    return out


def _first_entity_id(entities: list[Entity]) -> str | None:
    for entity in entities:
        if isinstance(entity, dict):
            entity_id = entity.get("id")
        else:
            entity_id = getattr(entity, "id", None)
        if isinstance(entity_id, str) and entity_id:
            return entity_id
    return None

