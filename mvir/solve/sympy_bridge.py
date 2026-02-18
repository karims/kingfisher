"""Best-effort MVIR Expr -> SymPy conversion."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mvir.core import ast

if TYPE_CHECKING:
    import sympy


def expr_to_sympy(
    expr: ast.Expr,
    sym_env: dict[str, "sympy.Symbol"] | None = None,
) -> tuple[object | None, list[str], dict[str, "sympy.Symbol"]]:
    """Convert an MVIR Expr to a SymPy object with non-fatal warnings."""

    try:
        import sympy
    except Exception:
        return None, ["sympy not installed"], sym_env or {}

    env: dict[str, sympy.Symbol] = {} if sym_env is None else sym_env
    warnings: list[str] = []

    def _fail(msg: str) -> tuple[object | None, list[str]]:
        return None, [msg]

    def _rec(node: ast.Expr) -> tuple[object | None, list[str]]:
        if isinstance(node, ast.Symbol):
            if node.id not in env:
                env[node.id] = sympy.Symbol(node.id)
            return env[node.id], []

        if isinstance(node, ast.Number):
            value = node.value
            if type(value) is int:
                return sympy.Integer(value), []
            if type(value) is float:
                return sympy.Float(value), []
            return _fail("unsupported Number value type")

        if isinstance(node, ast.Bool):
            return (sympy.true if node.value else sympy.false), []

        if isinstance(node, ast.Add):
            out_args: list[object] = []
            child_warnings: list[str] = []
            for arg in node.args:
                converted, w = _rec(arg)
                child_warnings.extend(w)
                if converted is None:
                    return None, child_warnings
                out_args.append(converted)
            return sympy.Add(*out_args), child_warnings

        if isinstance(node, ast.Mul):
            out_args = []
            child_warnings: list[str] = []
            for arg in node.args:
                converted, w = _rec(arg)
                child_warnings.extend(w)
                if converted is None:
                    return None, child_warnings
                out_args.append(converted)
            return sympy.Mul(*out_args), child_warnings

        if isinstance(node, ast.Div):
            num, num_w = _rec(node.num)
            den, den_w = _rec(node.den)
            child_warnings = num_w + den_w
            if num is None or den is None:
                return None, child_warnings
            return num / den, child_warnings

        if isinstance(node, ast.Pow):
            base, base_w = _rec(node.base)
            exp, exp_w = _rec(node.exp)
            child_warnings = base_w + exp_w
            if base is None or exp is None:
                return None, child_warnings
            return base**exp, child_warnings

        if isinstance(node, ast.Neg):
            arg, arg_w = _rec(node.arg)
            if arg is None:
                return None, arg_w
            return -arg, arg_w

        if isinstance(node, ast.Eq):
            lhs, lhs_w = _rec(node.lhs)
            rhs, rhs_w = _rec(node.rhs)
            child_warnings = lhs_w + rhs_w
            if lhs is None or rhs is None:
                return None, child_warnings
            return sympy.Eq(lhs, rhs), child_warnings

        if isinstance(node, ast.Neq):
            lhs, lhs_w = _rec(node.lhs)
            rhs, rhs_w = _rec(node.rhs)
            child_warnings = lhs_w + rhs_w
            if lhs is None or rhs is None:
                return None, child_warnings
            return sympy.Ne(lhs, rhs), child_warnings

        if isinstance(node, ast.Lt):
            lhs, lhs_w = _rec(node.lhs)
            rhs, rhs_w = _rec(node.rhs)
            child_warnings = lhs_w + rhs_w
            if lhs is None or rhs is None:
                return None, child_warnings
            return sympy.Lt(lhs, rhs), child_warnings

        if isinstance(node, ast.Le):
            lhs, lhs_w = _rec(node.lhs)
            rhs, rhs_w = _rec(node.rhs)
            child_warnings = lhs_w + rhs_w
            if lhs is None or rhs is None:
                return None, child_warnings
            return sympy.Le(lhs, rhs), child_warnings

        if isinstance(node, ast.Gt):
            lhs, lhs_w = _rec(node.lhs)
            rhs, rhs_w = _rec(node.rhs)
            child_warnings = lhs_w + rhs_w
            if lhs is None or rhs is None:
                return None, child_warnings
            return sympy.Gt(lhs, rhs), child_warnings

        if isinstance(node, ast.Ge):
            lhs, lhs_w = _rec(node.lhs)
            rhs, rhs_w = _rec(node.rhs)
            child_warnings = lhs_w + rhs_w
            if lhs is None or rhs is None:
                return None, child_warnings
            return sympy.Ge(lhs, rhs), child_warnings

        if isinstance(node, ast.Sum):
            if node.var not in env:
                env[node.var] = sympy.Symbol(node.var)
            index_sym = env[node.var]

            lower, lower_w = _rec(node.from_)
            upper, upper_w = _rec(node.to)
            body, body_w = _rec(node.body)
            child_warnings = lower_w + upper_w + body_w
            if lower is None or upper is None or body is None:
                return None, child_warnings
            return sympy.Sum(body, (index_sym, lower, upper)), child_warnings

        if isinstance(node, ast.Call):
            fn_map = {
                "sin": sympy.sin,
                "cos": sympy.cos,
                "tan": sympy.tan,
                "log": sympy.log,
                "exp": sympy.exp,
                "sqrt": sympy.sqrt,
                "abs": sympy.Abs,
            }
            mapped = fn_map.get(node.fn)
            if mapped is None:
                return _fail(f"unsupported Call fn={node.fn}")

            converted_args: list[object] = []
            child_warnings: list[str] = []
            for arg in node.args:
                converted, w = _rec(arg)
                child_warnings.extend(w)
                if converted is None:
                    return None, child_warnings
                converted_args.append(converted)
            return mapped(*converted_args), child_warnings

        return _fail(f"unsupported node={node.__class__.__name__}")

    converted, child_warnings = _rec(expr)
    warnings.extend(child_warnings)
    return converted, warnings, env
