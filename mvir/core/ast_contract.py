"""Internal AST shape contract checks before Pydantic Expr parsing."""

from __future__ import annotations

from copy import deepcopy

from mvir.core.models import Warning


_BINARY_NODES = {"Eq", "Neq", "Lt", "Le", "Gt", "Ge", "Divides"}
_NARY_NODES = {"Add", "Mul"}


def validate_expr_dict(expr: dict, *, allow_repair: bool) -> tuple[dict, list[Warning]]:
    """Validate/repair an Expr-like dict against internal AST shape contract.

    Returns a repaired copy (never mutates input) and warnings containing repair actions
    and contract errors. Contract errors use pydantic-like tuple paths in details.path.
    """

    warnings: list[Warning] = []
    if not isinstance(expr, dict):
        warnings.append(
            Warning(
                code="expr_contract_error",
                message="Expression must be an object.",
                trace=[],
                details={"path": tuple(), "reason": "not_object"},
            )
        )
        return {}, warnings

    repaired = _validate_node(deepcopy(expr), path=tuple(), allow_repair=allow_repair, warnings=warnings)
    if not isinstance(repaired, dict):
        return {}, warnings
    return repaired, warnings


def _validate_node(
    node: dict,
    *,
    path: tuple,
    allow_repair: bool,
    warnings: list[Warning],
) -> dict | None:
    node_name = node.get("node")
    if not isinstance(node_name, str):
        _error(warnings, path + ("node",), "missing_or_invalid_node")
        return None

    if node_name == "Symbol":
        out = {"node": "Symbol"}
        symbol_id = node.get("id")
        if (not isinstance(symbol_id, str) or not symbol_id) and allow_repair:
            name = node.get("name")
            if isinstance(name, str) and name:
                symbol_id = name
                _repair(warnings, path, "symbol_name_to_id")
        if not isinstance(symbol_id, str) or not symbol_id:
            _error(warnings, path + ("id",), "missing_required_field")
            return None
        out["id"] = symbol_id
        return out

    if node_name == "Number":
        if "value" not in node:
            _error(warnings, path + ("value",), "missing_required_field")
            return None
        return {"node": "Number", "value": node.get("value")}

    if node_name == "Bool":
        if "value" not in node:
            _error(warnings, path + ("value",), "missing_required_field")
            return None
        return {"node": "Bool", "value": node.get("value")}

    if node_name in _NARY_NODES:
        out = {"node": node_name}
        args = node.get("args")
        if not isinstance(args, list) and allow_repair and node_name == "Add":
            terms = node.get("terms")
            if isinstance(terms, list):
                args = terms
                _repair(warnings, path, "add_terms_to_args")
        if not isinstance(args, list):
            _error(warnings, path + ("args",), "missing_required_field")
            return None
        validated_args: list[dict] = []
        for idx, item in enumerate(args):
            if not isinstance(item, dict):
                _error(warnings, path + ("args", idx), "arg_not_object")
                continue
            validated = _validate_node(
                item,
                path=path + ("args", idx),
                allow_repair=allow_repair,
                warnings=warnings,
            )
            if validated is not None:
                validated_args.append(validated)
        if not validated_args:
            _error(warnings, path + ("args",), "empty_args")
            return None
        out["args"] = validated_args
        return out

    if node_name in _BINARY_NODES:
        out = {"node": node_name}
        lhs = node.get("lhs")
        rhs = node.get("rhs")
        if not isinstance(lhs, dict):
            _error(warnings, path + ("lhs",), "missing_required_field")
            return None
        if not isinstance(rhs, dict):
            _error(warnings, path + ("rhs",), "missing_required_field")
            return None
        lhs_v = _validate_node(lhs, path=path + ("lhs",), allow_repair=allow_repair, warnings=warnings)
        rhs_v = _validate_node(rhs, path=path + ("rhs",), allow_repair=allow_repair, warnings=warnings)
        if lhs_v is None or rhs_v is None:
            return None
        out["lhs"] = lhs_v
        out["rhs"] = rhs_v
        return out

    if node_name == "Div":
        out = {"node": "Div"}
        num = node.get("num")
        den = node.get("den")
        if not isinstance(num, dict):
            _error(warnings, path + ("num",), "missing_required_field")
            return None
        if not isinstance(den, dict):
            _error(warnings, path + ("den",), "missing_required_field")
            return None
        num_v = _validate_node(num, path=path + ("num",), allow_repair=allow_repair, warnings=warnings)
        den_v = _validate_node(den, path=path + ("den",), allow_repair=allow_repair, warnings=warnings)
        if num_v is None or den_v is None:
            return None
        out["num"] = num_v
        out["den"] = den_v
        return out

    if node_name == "Pow":
        out = {"node": "Pow"}
        base = node.get("base")
        exp = node.get("exp")
        if not isinstance(base, dict):
            _error(warnings, path + ("base",), "missing_required_field")
            return None
        if not isinstance(exp, dict):
            _error(warnings, path + ("exp",), "missing_required_field")
            return None
        base_v = _validate_node(base, path=path + ("base",), allow_repair=allow_repair, warnings=warnings)
        exp_v = _validate_node(exp, path=path + ("exp",), allow_repair=allow_repair, warnings=warnings)
        if base_v is None or exp_v is None:
            return None
        out["base"] = base_v
        out["exp"] = exp_v
        return out

    if node_name == "Neg":
        arg = node.get("arg")
        if not isinstance(arg, dict):
            _error(warnings, path + ("arg",), "missing_required_field")
            return None
        arg_v = _validate_node(arg, path=path + ("arg",), allow_repair=allow_repair, warnings=warnings)
        if arg_v is None:
            return None
        return {"node": "Neg", "arg": arg_v}

    if node_name == "Call":
        out = {"node": "Call"}
        fn = node.get("fn")
        args = node.get("args")
        if not isinstance(fn, str) or not fn:
            _error(warnings, path + ("fn",), "missing_required_field")
            return None
        if not isinstance(args, list):
            _error(warnings, path + ("args",), "missing_required_field")
            return None
        validated_args: list[dict] = []
        for idx, item in enumerate(args):
            if not isinstance(item, dict):
                _error(warnings, path + ("args", idx), "arg_not_object")
                continue
            validated = _validate_node(
                item,
                path=path + ("args", idx),
                allow_repair=allow_repair,
                warnings=warnings,
            )
            if validated is not None:
                validated_args.append(validated)
        if not validated_args:
            _error(warnings, path + ("args",), "empty_args")
            return None
        out["fn"] = fn
        out["args"] = validated_args
        return out

    if node_name == "Sum":
        out = {"node": "Sum"}
        var = node.get("var")
        frm = node.get("from")
        if frm is None and allow_repair and "from_" in node:
            frm = node.get("from_")
            _repair(warnings, path, "sum_from_alias_to_from")
        to = node.get("to")
        body = node.get("body")
        if not isinstance(var, str) or not var:
            _error(warnings, path + ("var",), "missing_required_field")
            return None
        if not isinstance(frm, dict):
            _error(warnings, path + ("from",), "missing_required_field")
            return None
        if not isinstance(to, dict):
            _error(warnings, path + ("to",), "missing_required_field")
            return None
        if not isinstance(body, dict):
            _error(warnings, path + ("body",), "missing_required_field")
            return None
        frm_v = _validate_node(frm, path=path + ("from",), allow_repair=allow_repair, warnings=warnings)
        to_v = _validate_node(to, path=path + ("to",), allow_repair=allow_repair, warnings=warnings)
        body_v = _validate_node(body, path=path + ("body",), allow_repair=allow_repair, warnings=warnings)
        if frm_v is None or to_v is None or body_v is None:
            return None
        out["var"] = var
        out["from"] = frm_v
        out["to"] = to_v
        out["body"] = body_v
        return out

    _error(warnings, path + ("node",), "unknown_node")
    return None


def _error(warnings: list[Warning], path: tuple, reason: str) -> None:
    warnings.append(
        Warning(
            code="expr_contract_error",
            message="Expression violates AST contract.",
            trace=[],
            details={"path": path, "reason": reason},
        )
    )


def _repair(warnings: list[Warning], path: tuple, repair: str) -> None:
    warnings.append(
        Warning(
            code="expr_contract_repair",
            message="Applied AST contract repair.",
            trace=[],
            details={"path": path, "repair": repair},
        )
    )

