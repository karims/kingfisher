"""Solver bundle export (MVIR -> solver-friendly payload)."""

from __future__ import annotations

from typing import Any


def _sympy_available() -> bool:
    try:
        import sympy as _  # noqa: F401

        return True
    except Exception:
        return False


def _expr_to_sympy_str_with_warning(expr_dict: dict[str, Any] | None) -> tuple[str | None, str | None]:
    if expr_dict is None:
        return None, "missing expression"

    if not _sympy_available():
        return None, "sympy not installed"

    def _rec(node: dict[str, Any]) -> str:
        node_type = node.get("node")
        if not isinstance(node_type, str):
            raise ValueError("expr node is missing 'node' discriminator")

        if node_type == "Symbol":
            symbol_id = node.get("id")
            if not isinstance(symbol_id, str) or not symbol_id:
                raise ValueError("Symbol.id missing")
            return symbol_id
        if node_type == "Number":
            value = node.get("value")
            if isinstance(value, (int, float)):
                return repr(value)
            raise ValueError("Number.value missing")
        if node_type in {"Bool", "True", "False"}:
            value = node.get("value")
            if isinstance(value, bool):
                return "True" if value else "False"
            return "True" if node_type == "True" else "False"
        if node_type == "Add":
            args = node.get("args")
            if not isinstance(args, list) or not args:
                raise ValueError("Add.args missing")
            if not all(isinstance(arg, dict) for arg in args):
                raise ValueError("Add.args contains non-expression item")
            return "Add(" + ", ".join(_rec(arg) for arg in args) + ")"
        if node_type == "Mul":
            args = node.get("args")
            if not isinstance(args, list) or not args:
                raise ValueError("Mul.args missing")
            if not all(isinstance(arg, dict) for arg in args):
                raise ValueError("Mul.args contains non-expression item")
            return "Mul(" + ", ".join(_rec(arg) for arg in args) + ")"
        if node_type == "Div":
            num = node.get("num")
            den = node.get("den")
            if not isinstance(num, dict) or not isinstance(den, dict):
                raise ValueError("Div.num/den missing")
            return f"({_rec(num)})/({_rec(den)})"
        if node_type == "Pow":
            base = node.get("base")
            exp = node.get("exp")
            if not isinstance(base, dict) or not isinstance(exp, dict):
                raise ValueError("Pow.base/exp missing")
            return f"Pow({_rec(base)}, {_rec(exp)})"
        if node_type == "Neg":
            arg = node.get("arg")
            if not isinstance(arg, dict):
                raise ValueError("Neg.arg missing")
            return f"(-({_rec(arg)}))"
        if node_type in {"Eq", "Neq", "Lt", "Le", "Gt", "Ge", "Divides"}:
            lhs = node.get("lhs")
            rhs = node.get("rhs")
            if not isinstance(lhs, dict) or not isinstance(rhs, dict):
                raise ValueError(f"{node_type}.lhs/rhs missing")
            lhs_s = _rec(lhs)
            rhs_s = _rec(rhs)
            if node_type == "Eq":
                return f"Eq({lhs_s}, {rhs_s})"
            if node_type == "Neq":
                return f"Ne({lhs_s}, {rhs_s})"
            if node_type == "Lt":
                return f"Lt({lhs_s}, {rhs_s})"
            if node_type == "Le":
                return f"Le({lhs_s}, {rhs_s})"
            if node_type == "Gt":
                return f"Gt({lhs_s}, {rhs_s})"
            if node_type == "Ge":
                return f"Ge({lhs_s}, {rhs_s})"
            return f"Eq(Mod({rhs_s}, {lhs_s}), 0)"
        if node_type == "Sum":
            var = node.get("var")
            lower = node.get("from")
            upper = node.get("to")
            body = node.get("body")
            if (
                not isinstance(var, str)
                or not isinstance(lower, dict)
                or not isinstance(upper, dict)
                or not isinstance(body, dict)
            ):
                raise ValueError("Sum missing var/from/to/body")
            return f"Sum({_rec(body)}, ({var}, {_rec(lower)}, {_rec(upper)}))"
        if node_type == "Call":
            fn = node.get("fn")
            args = node.get("args")
            if not isinstance(fn, str) or not isinstance(args, list):
                raise ValueError("Call.fn/args missing")
            if not all(isinstance(arg, dict) for arg in args):
                raise ValueError("Call.args contains non-expression item")
            rendered_args = ", ".join(_rec(arg) for arg in args)
            if fn in {"sin", "cos", "tan", "log", "exp", "sqrt", "Abs"}:
                return f"{fn}({rendered_args})"
            return f"Function('{fn}')({rendered_args})"

        raise ValueError(f"unsupported node: {node_type}")

    try:
        return _rec(expr_dict), None
    except Exception as exc:  # noqa: BLE001 - best effort export path
        return None, str(exc)


def expr_to_sympy_str(expr_dict: dict) -> str | None:
    """Convert an MVIR expression dict to a best-effort SymPy expression string."""

    rendered, _warning = _expr_to_sympy_str_with_warning(expr_dict)
    return rendered


def build_solver_bundle(mvir: dict) -> dict:
    """Build solver-oriented bundle from validated MVIR payload dict."""

    meta = mvir.get("meta", {})
    entities = mvir.get("entities", [])
    goal = mvir.get("goal", {})
    assumptions = mvir.get("assumptions", [])
    source = mvir.get("source", {})

    out_entities: list[dict] = []
    if isinstance(entities, list):
        for entity in entities:
            if not isinstance(entity, dict):
                continue
            out_entities.append(
                {
                    "id": entity.get("id"),
                    "kind": entity.get("kind"),
                    "type": entity.get("type"),
                }
            )
    out_entities = sorted(out_entities, key=lambda item: str(item.get("id", "")))

    sympy_failures = 0
    had_sympy = False

    goal_expr = goal.get("expr") if isinstance(goal, dict) else None
    goal_expr_sympy, goal_expr_warning = _expr_to_sympy_str_with_warning(
        goal_expr if isinstance(goal_expr, dict) else None
    )
    goal_target = goal.get("target") if isinstance(goal, dict) else None
    goal_target_sympy, goal_target_warning = _expr_to_sympy_str_with_warning(
        goal_target if isinstance(goal_target, dict) else None
    ) if goal_target is not None else (None, None)
    goal_warnings: list[str] = []
    if goal_expr_warning is not None:
        goal_warnings.append(f"goal expr: {goal_expr_warning}")
        sympy_failures += 1
    if goal_target is not None and goal_target_warning is not None:
        goal_warnings.append(f"goal target: {goal_target_warning}")
        sympy_failures += 1
    if goal_expr_sympy is not None or goal_target_sympy is not None:
        had_sympy = True

    out_assumptions: list[dict] = []
    if isinstance(assumptions, list):
        for assumption in assumptions:
            if not isinstance(assumption, dict):
                continue
            expr = assumption.get("expr")
            rendered, warning = _expr_to_sympy_str_with_warning(expr if isinstance(expr, dict) else None)
            assumption_warnings: list[str] = []
            if warning is not None:
                assumption_warnings.append(warning)
                sympy_failures += 1
            if rendered is not None:
                had_sympy = True
            out_assumptions.append(
                {
                    "kind": assumption.get("kind"),
                    "expr_sympy": rendered,
                    "expr_mvir": expr if isinstance(expr, dict) else {},
                    "warnings": assumption_warnings,
                }
            )

    math_surface = source.get("math_surface") if isinstance(source, dict) else None
    math_surface_count = len(math_surface) if isinstance(math_surface, list) else 0

    return {
        "meta": {
            "id": meta.get("id") if isinstance(meta, dict) else None,
            "version": meta.get("version") if isinstance(meta, dict) else None,
        },
        "entities": out_entities,
        "goal": {
            "kind": goal.get("kind") if isinstance(goal, dict) else None,
            "expr_sympy": goal_expr_sympy,
            "expr_mvir": goal_expr if isinstance(goal_expr, dict) else {},
            "target_sympy": goal_target_sympy,
            "warnings": goal_warnings,
        },
        "assumptions": out_assumptions,
        "surface": {"math_surface_count": math_surface_count},
        "stats": {
            "had_sympy": had_sympy,
            "sympy_failures": sympy_failures,
        },
    }
