"""Deterministic normalization helpers for AST-like payloads."""

from __future__ import annotations

import re
from copy import deepcopy

from mvir.core.ast_contract import validate_expr_dict
from mvir.core.models import Warning
from mvir.core.operators import DEFAULT_REGISTRY


_REL_NODES = {"Eq", "Neq", "Lt", "Le", "Gt", "Ge", "Divides"}
_BOOL_NODES = {"Bool", "True", "False"}


def normalize_any(x):
    """Normalize any python object recursively for MVIR Expr shapes."""

    if isinstance(x, list):
        return [normalize_any(v) for v in x]
    if isinstance(x, dict):
        return normalize_expr_dict(x)
    return x


def normalize_expr_dict_with_warnings(data: dict) -> tuple[dict | None, list[Warning]]:
    """Normalize + validate an Expr-like dict and return (expr, warnings)."""

    warnings: list[Warning] = []
    raw = _normalize_expr_dict_raw(data, warnings=warnings)
    if not isinstance(raw, dict):
        return None, warnings

    validated, contract_warnings = validate_expr_dict(raw, allow_repair=True)
    warnings.extend(contract_warnings)
    if not validated:
        return None, warnings
    return validated, warnings


def normalize_expr_dict_relaxed(data: dict) -> dict | None:
    """Normalize only keys/shapes without enforcing required-field contract."""

    warnings: list[Warning] = []
    return _normalize_expr_dict_raw(data, warnings=warnings)


def normalize_expr_dict(data: dict) -> dict | None:
    """Normalize a dict into a parse_expr-friendly Expr-like dict."""

    normalized, _warnings = normalize_expr_dict_with_warnings(data)
    return normalized


def _normalize_expr_dict_raw(data: dict, *, warnings: list[Warning]) -> dict | None:
    """Legacy key normalization pass (before contract validator)."""

    if not isinstance(data, dict):
        return data

    raw = deepcopy(data)
    node = raw.get("node")
    if not isinstance(node, str):
        return None
    canonical_node = _canonicalize_node_name(node)
    if canonical_node is None:
        return None
    if canonical_node != node:
        warnings.append(
            Warning(
                code="expr_normalize_repair",
                message="Normalized node alias to canonical AST node.",
                trace=[],
                details={
                    "path": ("node",),
                    "repair": "node_alias_to_canonical",
                    "from": node,
                    "to": canonical_node,
                },
            )
        )
    node = canonical_node

    if node == "Symbol":
        out: dict = {"node": "Symbol"}
        symbol_id = raw.get("id")
        if not symbol_id and isinstance(raw.get("name"), str):
            symbol_id = raw.get("name")
        if isinstance(symbol_id, str) and symbol_id:
            out["id"] = symbol_id
        return out

    if node in _REL_NODES:
        lhs = raw.get("lhs")
        rhs = raw.get("rhs")
        args = _first_list(raw, "args", "operands", "children")
        if (lhs is None or rhs is None) and isinstance(args, list):
            if lhs is None and len(args) >= 1:
                lhs = args[0]
            if rhs is None and len(args) >= 2:
                rhs = args[1]
        if lhs is None and "left" in raw:
            lhs = raw.get("left")
        if rhs is None and "right" in raw:
            rhs = raw.get("right")
        out = {"node": node}
        if lhs is not None:
            out["lhs"] = _normalize_any_raw(lhs, warnings=warnings)
        if rhs is not None:
            out["rhs"] = _normalize_any_raw(rhs, warnings=warnings)
        return out

    if node in {"Add", "Mul"}:
        args = _first_list(raw, "args", "terms", "factors", "operands", "children")
        if not isinstance(args, list):
            lhs = raw.get("lhs")
            rhs = raw.get("rhs")
            if lhs is None and "left" in raw:
                lhs = raw.get("left")
            if rhs is None and "right" in raw:
                rhs = raw.get("right")
            if lhs is not None and rhs is not None:
                args = [lhs, rhs]
        out = {"node": node}
        if isinstance(args, list):
            norm_args = [_normalize_any_raw(a, warnings=warnings) for a in args]
            out["args"] = _flatten_same_op(node, norm_args)
        return out

    if node == "Pow":
        base = raw.get("base")
        exp = raw.get("exp")
        if base is None and "left" in raw:
            base = raw.get("left")
        if exp is None and "right" in raw:
            exp = raw.get("right")
        args = _first_list(raw, "args", "operands", "children")
        if (base is None or exp is None) and isinstance(args, list):
            if base is None and len(args) >= 1:
                base = args[0]
            if exp is None and len(args) >= 2:
                exp = args[1]
        out = {"node": "Pow"}
        if base is not None:
            out["base"] = _normalize_any_raw(base, warnings=warnings)
        if exp is not None:
            out["exp"] = _normalize_any_raw(exp, warnings=warnings)
        return out

    if node == "Div":
        num = raw.get("num")
        den = raw.get("den")
        if num is None and "left" in raw:
            num = raw.get("left")
        if den is None and "right" in raw:
            den = raw.get("right")
        if num is None and "lhs" in raw:
            num = raw.get("lhs")
        if den is None and "rhs" in raw:
            den = raw.get("rhs")
        args = _first_list(raw, "args", "operands", "children")
        if (num is None or den is None) and isinstance(args, list):
            if num is None and len(args) >= 1:
                num = args[0]
            if den is None and len(args) >= 2:
                den = args[1]
        out = {"node": "Div"}
        if num is not None:
            out["num"] = _normalize_any_raw(num, warnings=warnings)
        if den is not None:
            out["den"] = _normalize_any_raw(den, warnings=warnings)
        return out

    if node == "Neg":
        arg = raw.get("arg")
        if arg is None and "value" in raw:
            arg = raw.get("value")
        args = _first_list(raw, "args", "operands", "children")
        if arg is None and isinstance(args, list) and len(args) >= 1:
            arg = args[0]
        out = {"node": "Neg"}
        if arg is not None:
            out["arg"] = _normalize_any_raw(arg, warnings=warnings)
        return out

    if node == "Number":
        out = {"node": "Number"}
        value = raw.get("value")
        if value is None and "val" in raw:
            value = raw.get("val")
        value = _parse_numeric(value)
        if value is not None:
            out["value"] = value
        return out

    if node in _BOOL_NODES:
        out = {"node": "Bool"}
        if node == "True":
            out["value"] = True
            return out
        if node == "False":
            out["value"] = False
            return out
        value = raw.get("value")
        coerced = _coerce_bool(value)
        if coerced is not None:
            out["value"] = coerced
        return out

    if node == "Call":
        out = {"node": "Call"}
        fn = raw.get("fn")
        if not isinstance(fn, str):
            name = raw.get("name")
            if isinstance(name, str):
                fn = name
        if isinstance(fn, str) and fn:
            out["fn"] = fn
        args = _first_list(raw, "args", "operands", "children")
        if isinstance(args, list):
            out["args"] = [_normalize_any_raw(a, warnings=warnings) for a in args]
        return out

    if node == "Sum":
        out = {"node": "Sum"}
        var = raw.get("var")
        if isinstance(var, str):
            out["var"] = var
        frm = raw.get("from")
        if frm is None and "from_" in raw:
            frm = raw.get("from_")
        to = raw.get("to")
        body = raw.get("body")
        if frm is not None:
            out["from"] = _normalize_any_raw(frm, warnings=warnings)
        if to is not None:
            out["to"] = _normalize_any_raw(to, warnings=warnings)
        if body is not None:
            out["body"] = _normalize_any_raw(body, warnings=warnings)
        return out

    # Unknown node: recurse values but keep shape.
    return None


def normalize_expr(obj: dict) -> dict:
    """Backward-compatible alias for callers using old function name."""

    return normalize_expr_dict(obj)


def _normalize_any_raw(value, *, warnings: list[Warning]):
    if isinstance(value, list):
        return [_normalize_any_raw(v, warnings=warnings) for v in value]
    if isinstance(value, dict):
        return _normalize_expr_dict_raw(value, warnings=warnings)
    return value


def _flatten_same_op(node: str, args: list) -> list:
    flat: list = []
    for arg in args:
        if isinstance(arg, dict) and arg.get("node") == node and isinstance(arg.get("args"), list):
            flat.extend(arg["args"])
        elif isinstance(arg, dict):
            flat.append(arg)
    return flat


def _first_list(raw: dict, *keys: str):
    for key in keys:
        value = raw.get(key)
        if isinstance(value, list):
            return value
    return None


def _parse_numeric(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        text = value.strip()
        if re.fullmatch(r"[+-]?\d+", text):
            try:
                return int(text)
            except ValueError:
                return None
        if re.fullmatch(r"[+-]?(?:\d+\.\d*|\d*\.\d+)", text):
            try:
                return float(text)
            except ValueError:
                return None
    return None


def _coerce_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text == "true":
            return True
        if text == "false":
            return False
    return None


def _canonicalize_node_name(node: str) -> str | None:
    if node in {
        "Symbol",
        "Number",
        "Bool",
        "True",
        "False",
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
    }:
        return node
    if DEFAULT_REGISTRY.canonical(node) is not None or node in _BOOL_NODES:
        return node
    # Direct surface lookup for aliases like "lt" or symbolic forms.
    by_surface = DEFAULT_REGISTRY.lookup(node)
    if by_surface is not None:
        return by_surface.ast_node
    lowered = node.lower()
    by_surface = DEFAULT_REGISTRY.lookup(lowered)
    if by_surface is not None:
        return by_surface.ast_node
    for candidate in DEFAULT_REGISTRY.all_nodes():
        if candidate.lower() == lowered:
            return candidate
    return None
