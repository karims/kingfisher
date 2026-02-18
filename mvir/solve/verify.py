"""Minimal verification helpers for solver outputs."""

from __future__ import annotations

from typing import TYPE_CHECKING

import sympy

if TYPE_CHECKING:
    from sympy.core.relational import Relational
    from sympy.core.expr import Expr


def parse_sympy_expr(s: str, symbols: dict[str, sympy.Symbol]) -> "Expr | Relational":
    """Parse a SymPy expression/relation string with a provided symbol table."""

    local_dict: dict[str, object] = {
        **symbols,
        "Eq": sympy.Eq,
        "Ne": sympy.Ne,
        "Lt": sympy.Lt,
        "Le": sympy.Le,
        "Gt": sympy.Gt,
        "Ge": sympy.Ge,
        "Abs": sympy.Abs,
        "sqrt": sympy.sqrt,
        "log": sympy.log,
        "exp": sympy.exp,
        "sin": sympy.sin,
        "cos": sympy.cos,
        "tan": sympy.tan,
    }
    return sympy.sympify(s, locals=local_dict)


def verify_constraints(
    constraints: list[str],
    symbols: dict[str, sympy.Symbol],
    subs: dict[str, int | float],
) -> tuple[bool, list[str]]:
    """Verify all constraints under substitutions; collect failure reasons."""

    failed: list[str] = []
    for constraint_s in constraints:
        try:
            parsed = parse_sympy_expr(constraint_s, symbols)
        except Exception as exc:  # noqa: BLE001 - defensive parser boundary
            failed.append(f"{constraint_s} (parse_error: {exc})")
            continue

        try:
            evaluated = parsed.subs(subs)
            simplified = sympy.simplify(evaluated)
            if simplified == sympy.true:
                continue
            if simplified == sympy.false:
                failed.append(constraint_s)
                continue

            if getattr(simplified, "is_Relational", False):
                failed.append(f"{constraint_s} (undetermined after substitution)")
                continue

            failed.append(f"{constraint_s} (not boolean)")
        except Exception as exc:  # noqa: BLE001 - defensive evaluation boundary
            failed.append(f"{constraint_s} (eval_error: {exc})")

    return len(failed) == 0, failed


def try_evaluate(
    expr_s: str,
    symbols: dict[str, sympy.Symbol],
    subs: dict[str, int | float],
) -> tuple[float | None, str | None]:
    """Best-effort numeric evaluation of a SymPy expression string."""

    try:
        parsed = parse_sympy_expr(expr_s, symbols)
    except Exception as exc:  # noqa: BLE001 - defensive parser boundary
        return None, f"parse_error: {exc}"

    if getattr(parsed, "is_Relational", False):
        return None, "expression is relational, not numeric"

    try:
        evaluated = sympy.N(parsed.subs(subs))
        if not bool(getattr(evaluated, "is_number", False)):
            return None, "expression did not evaluate to a number"
        return float(evaluated), None
    except Exception as exc:  # noqa: BLE001 - defensive evaluation boundary
        return None, f"eval_error: {exc}"
