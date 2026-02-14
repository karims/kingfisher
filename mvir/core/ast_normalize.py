"""Deterministic normalization helpers for AST-like dict payloads."""

from __future__ import annotations

from copy import deepcopy


_COMPARISON_NODES = {"Eq", "Neq", "Lt", "Le", "Gt", "Ge", "Divides"}


def normalize_expr(obj: dict) -> dict:
    """Normalize common near-valid Expr dict shapes into MVIR AST shapes."""

    def _norm(value):
        if isinstance(value, list):
            return [_norm(item) for item in value]
        if not isinstance(value, dict):
            return value

        node = value.get("node")
        out = {k: _norm(v) for k, v in value.items()}

        if node == "Symbol" and "id" not in out and isinstance(out.get("name"), str):
            out["id"] = out.pop("name")

        if node == "Number" and "value" not in out and "val" in out:
            out["value"] = out.pop("val")

        if node in _COMPARISON_NODES:
            args = out.get("args")
            if (
                isinstance(args, list)
                and len(args) >= 2
                and "lhs" not in out
                and "rhs" not in out
            ):
                out["lhs"] = args[0]
                out["rhs"] = args[1]
                out.pop("args", None)

        if node in {"Add", "Mul"}:
            has_args = isinstance(out.get("args"), list)
            if not has_args and "lhs" in out and "rhs" in out:
                out["args"] = [out["lhs"], out["rhs"]]
                out.pop("lhs", None)
                out.pop("rhs", None)

        if node == "Pow":
            args = out.get("args")
            if (
                isinstance(args, list)
                and len(args) >= 2
                and "base" not in out
                and "exp" not in out
            ):
                out["base"] = args[0]
                out["exp"] = args[1]
                out.pop("args", None)

        return out

    if not isinstance(obj, dict):
        return obj
    return _norm(deepcopy(obj))

