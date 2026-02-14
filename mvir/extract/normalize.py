"""Deterministic normalization for near-MVIR LLM payloads."""

from __future__ import annotations

from copy import deepcopy


_GOAL_KINDS = {
    "prove",
    "find",
    "compute",
    "maximize",
    "minimize",
    "exists",
    "counterexample",
}

_CONCEPT_ROLES = {
    "domain",
    "pattern",
    "candidate_tool",
    "definition",
    "representation_hint",
}

_ASSUMPTION_KINDS = {"given", "derived", "wlog"}


def normalize_llm_payload(payload: dict) -> dict:
    """Normalize known near-valid payload patterns deterministically."""

    data = deepcopy(payload)

    assumptions = data.get("assumptions")
    if isinstance(assumptions, list):
        for item in assumptions:
            if not isinstance(item, dict):
                continue
            item["expr"] = _normalize_expr(item.get("expr"))
            kind = item.get("kind")
            if not isinstance(kind, str) or kind not in _ASSUMPTION_KINDS:
                item["kind"] = "given"

    goal = data.get("goal")
    if isinstance(goal, list):
        selected_idx = _select_goal_index(goal)
        selected = goal[selected_idx] if selected_idx is not None else {}
        normalized_goal = _normalize_goal_item(selected)
        data["goal"] = normalized_goal
        if len(goal) > 1:
            warnings = data.get("warnings")
            if not isinstance(warnings, list):
                warnings = []
                data["warnings"] = warnings
            warnings.append(
                {
                    "code": "dropped_goals",
                    "message": f"Dropped {len(goal) - 1} secondary goal candidates.",
                    "trace": normalized_goal.get("trace", ["s0"]),
                }
            )
    elif isinstance(goal, dict):
        if "expr" in goal:
            goal["expr"] = _normalize_expr(goal.get("expr"))
        if "target" in goal:
            goal["target"] = _normalize_expr(goal.get("target"))

    concepts = data.get("concepts")
    if isinstance(concepts, list):
        for item in concepts:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            if not isinstance(role, str) or role not in _CONCEPT_ROLES:
                item["role"] = "definition"

    warnings = data.get("warnings")
    if isinstance(warnings, list):
        for item in warnings:
            if not isinstance(item, dict):
                continue
            code = item.get("code")
            if not isinstance(code, str) or not code:
                item["code"] = "unspecified"

    return data


def _select_goal_index(goal_items: list) -> int | None:
    for i, item in enumerate(goal_items):
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        role = item.get("role")
        if (isinstance(kind, str) and "prove" in kind.lower()) or (
            isinstance(role, str) and "prove" in role.lower()
        ):
            return i
    return 0 if goal_items else None


def _normalize_goal_item(item: object) -> dict:
    if not isinstance(item, dict):
        return {
            "kind": "prove",
            "expr": {"node": "Bool", "value": True},
            "trace": ["s0"],
        }
    kind = item.get("kind")
    if not isinstance(kind, str) or kind not in _GOAL_KINDS:
        role = item.get("role")
        if isinstance(role, str) and "prove" in role.lower():
            kind = "prove"
        else:
            kind = "prove"

    expr = _normalize_expr(item.get("expr"))
    if not isinstance(expr, dict):
        expr = {"node": "Bool", "value": True}

    trace = item.get("trace")
    if isinstance(trace, list) and all(isinstance(t, str) for t in trace):
        goal_trace = trace
    else:
        goal_trace = ["s0"]

    out = {"kind": kind, "expr": expr, "trace": goal_trace}
    if "target" in item:
        out["target"] = _normalize_expr(item.get("target"))
    return out


def _normalize_expr(value):
    if isinstance(value, list):
        return [_normalize_expr(v) for v in value]
    if not isinstance(value, dict):
        return value

    node = value.get("node")
    if node == "var" and isinstance(value.get("name"), str):
        return {"node": "Symbol", "id": value["name"]}
    if node == "const" and "value" in value:
        return {"node": "Number", "value": value["value"]}

    op = value.get("op")
    if isinstance(op, str):
        left = _normalize_expr(value.get("left"))
        right = _normalize_expr(value.get("right"))
        if op == ">":
            return {"node": "Gt", "lhs": left, "rhs": right}
        if op == ">=":
            return {"node": "Ge", "lhs": left, "rhs": right}
        if op in {"=", "=="}:
            return {"node": "Eq", "lhs": left, "rhs": right}
        if op == "+":
            return {"node": "Add", "args": [left, right]}
        if op == "^":
            return {"node": "Pow", "base": left, "exp": right}

    normalized = {}
    for k, v in value.items():
        normalized[k] = _normalize_expr(v)
    return normalized

