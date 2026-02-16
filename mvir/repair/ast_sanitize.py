"""Deterministic sanitizer for partial Expr dicts."""

from __future__ import annotations

from copy import deepcopy


_BINARY_NODES = {"Eq", "Gt", "Ge", "Lt", "Le", "Neq", "Divides"}
_NARY_NODES = {"Add", "Mul"}


def sanitize_expr_dict(data: dict) -> dict | None:
    """Sanitize an Expr-like dict; return None when required fields are missing."""

    if not isinstance(data, dict):
        return None

    raw = deepcopy(data)
    cleaned = _drop_none_values(raw)

    node = cleaned.get("node")
    if not isinstance(node, str):
        return None

    out: dict = {"node": node}

    if node == "Symbol":
        symbol_id = cleaned.get("id")
        if not isinstance(symbol_id, str) or not symbol_id:
            return None
        out["id"] = symbol_id
        return out

    if node == "Number":
        if "value" not in cleaned:
            return None
        out["value"] = cleaned["value"]
        return out

    if node == "Bool":
        if "value" not in cleaned:
            return None
        out["value"] = cleaned["value"]
        return out

    if node in _NARY_NODES:
        args = cleaned.get("args")
        if not isinstance(args, list):
            return None
        sanitized_args = _sanitize_expr_list(args)
        if not sanitized_args:
            return None
        out["args"] = sanitized_args
        return out

    if node in _BINARY_NODES:
        lhs = _sanitize_required_expr_field(cleaned.get("lhs"))
        rhs = _sanitize_required_expr_field(cleaned.get("rhs"))
        if lhs is None or rhs is None:
            return None
        out["lhs"] = lhs
        out["rhs"] = rhs
        return out

    if node == "Pow":
        base = _sanitize_required_expr_field(cleaned.get("base"))
        exp = _sanitize_required_expr_field(cleaned.get("exp"))
        if base is None or exp is None:
            return None
        out["base"] = base
        out["exp"] = exp
        return out

    if node == "Div":
        num = _sanitize_required_expr_field(cleaned.get("num"))
        den = _sanitize_required_expr_field(cleaned.get("den"))
        if num is None or den is None:
            return None
        out["num"] = num
        out["den"] = den
        return out

    if node == "Neg":
        arg = _sanitize_required_expr_field(cleaned.get("arg"))
        if arg is None:
            return None
        out["arg"] = arg
        return out

    if node == "Sum":
        var = cleaned.get("var")
        frm = _sanitize_required_expr_field(cleaned.get("from"))
        to = _sanitize_required_expr_field(cleaned.get("to"))
        body = _sanitize_required_expr_field(cleaned.get("body"))
        if not isinstance(var, str) or not var:
            return None
        if frm is None or to is None or body is None:
            return None
        out["var"] = var
        out["from"] = frm
        out["to"] = to
        out["body"] = body
        return out

    if node == "Call":
        fn = cleaned.get("fn")
        args = cleaned.get("args")
        if not isinstance(fn, str) or not fn or not isinstance(args, list):
            return None
        sanitized_args = _sanitize_expr_list(args)
        if not sanitized_args:
            return None
        out["fn"] = fn
        out["args"] = sanitized_args
        return out

    return None


def _drop_none_values(value):
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if v is None:
                continue
            out[k] = _drop_none_values(v)
        return out
    if isinstance(value, list):
        return [_drop_none_values(v) for v in value]
    return value


def _sanitize_required_expr_field(value) -> dict | None:
    if not isinstance(value, dict):
        return None
    return sanitize_expr_dict(value)


def _sanitize_expr_list(values: list) -> list[dict]:
    out: list[dict] = []
    for value in values:
        sanitized = _sanitize_required_expr_field(value)
        if sanitized is None:
            continue
        out.append(sanitized)
    return out
