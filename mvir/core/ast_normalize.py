"""Deterministic normalization helpers for AST-like payloads."""

from __future__ import annotations

import re
from copy import deepcopy


_REL_NODES = {"Eq", "Neq", "Lt", "Le", "Gt", "Ge", "Divides"}


def normalize_any(x):
    """Normalize any python object recursively for MVIR Expr shapes."""

    if isinstance(x, list):
        return [normalize_any(v) for v in x]
    if isinstance(x, dict):
        return normalize_expr_dict(x)
    return x


def normalize_expr_dict(data: dict) -> dict | None:
    """Normalize a dict into a parse_expr-friendly Expr-like dict."""

    if not isinstance(data, dict):
        return data

    raw = deepcopy(data)
    node = raw.get("node")
    if not isinstance(node, str):
        return None

    if node == "Symbol":
        out: dict = {"node": "Symbol"}
        symbol_id = raw.get("id")
        if not symbol_id and isinstance(raw.get("name"), str):
            symbol_id = raw.get("name")
        if isinstance(symbol_id, str) and symbol_id:
            out["id"] = symbol_id
            return out
        return None

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
            out["lhs"] = normalize_any(lhs)
        if rhs is not None:
            out["rhs"] = normalize_any(rhs)
        if "lhs" not in out or "rhs" not in out:
            return None
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
            norm_args = [normalize_any(a) for a in args]
            out["args"] = _flatten_same_op(node, norm_args)
        if not isinstance(out.get("args"), list):
            return None
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
            out["base"] = normalize_any(base)
        if exp is not None:
            out["exp"] = normalize_any(exp)
        if "base" not in out or "exp" not in out:
            return None
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
            out["num"] = normalize_any(num)
        if den is not None:
            out["den"] = normalize_any(den)
        if "num" not in out or "den" not in out:
            return None
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
            out["arg"] = normalize_any(arg)
            return out
        return None

    if node == "Number":
        out = {"node": "Number"}
        value = raw.get("value")
        if value is None and "val" in raw:
            value = raw.get("val")
        value = _parse_numeric(value)
        if value is not None:
            out["value"] = value
            return out
        return None

    if node in {"Bool", "True", "False"}:
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
        return None

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
            out["args"] = [normalize_any(a) for a in args]
        if not isinstance(out.get("args"), list) or not out.get("args"):
            return None
        if "fn" not in out:
            return None
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
            out["from"] = normalize_any(frm)
        if to is not None:
            out["to"] = normalize_any(to)
        if body is not None:
            out["body"] = normalize_any(body)
        if not isinstance(out.get("var"), str) or not out.get("var"):
            return None
        if "from" not in out or "to" not in out or "body" not in out:
            return None
        return out

    # Unknown node: recurse values but keep shape.
    return None


def normalize_expr(obj: dict) -> dict:
    """Backward-compatible alias for callers using old function name."""

    return normalize_expr_dict(obj)


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
