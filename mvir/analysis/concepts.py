"""Deterministic concept extraction from MVIR AST patterns."""

from __future__ import annotations

from mvir.core.ast import Div, Eq, Expr, Ge, Gt, Mul, Number, Pow, Sum, Symbol, Add
from mvir.core.models import Assumption, Concept, ConceptRole, Goal, MVIR


def _is_number(expr: Expr, value: float) -> bool:
    return isinstance(expr, Number) and float(expr.value) == value


def _match_nonnegativity_of_square(expr: Expr) -> str | None:
    if not isinstance(expr, Ge):
        return None
    if not _is_number(expr.rhs, 0.0):
        return None
    if not isinstance(expr.lhs, Pow):
        return None
    if not isinstance(expr.lhs.base, Symbol):
        return None
    if not _is_number(expr.lhs.exp, 2.0):
        return None
    return expr.lhs.base.id


def _match_sum_of_first_n_integers(expr: Expr) -> bool:
    if not isinstance(expr, Eq):
        return False
    if not isinstance(expr.lhs, Sum):
        return False
    lhs = expr.lhs
    if lhs.var != "k":
        return False
    if not _is_number(lhs.from_, 1.0):
        return False
    if not (isinstance(lhs.to, Symbol) and lhs.to.id == "n"):
        return False
    if not (isinstance(lhs.body, Symbol) and lhs.body.id == "k"):
        return False

    rhs = expr.rhs
    if not isinstance(rhs, Div):
        return False
    if not _is_number(rhs.den, 2.0):
        return False
    if not isinstance(rhs.num, Mul) or len(rhs.num.args) != 2:
        return False
    mul_symbol_n = next(
        (arg for arg in rhs.num.args if isinstance(arg, Symbol) and arg.id == "n"),
        None,
    )
    mul_add_n_plus_1 = next(
        (arg for arg in rhs.num.args if isinstance(arg, Add) and len(arg.args) == 2),
        None,
    )
    if mul_symbol_n is None or mul_add_n_plus_1 is None:
        return False

    add_has_symbol_n = any(
        isinstance(arg, Symbol) and arg.id == "n" for arg in mul_add_n_plus_1.args
    )
    add_has_one = any(_is_number(arg, 1.0) for arg in mul_add_n_plus_1.args)
    if not (add_has_symbol_n and add_has_one):
        return False
    return True


def _match_positive_variable(expr: Expr) -> str | None:
    if not isinstance(expr, Gt):
        return None
    if not isinstance(expr.lhs, Symbol):
        return None
    if not _is_number(expr.rhs, 0.0):
        return None
    return expr.lhs.id


def _match_goal(goal: Goal) -> list[Concept]:
    out: list[Concept] = []
    var = _match_nonnegativity_of_square(goal.expr)
    if var is not None:
        out.append(
            Concept(
                id="nonnegativity_of_square",
                role=ConceptRole.PATTERN,
                trigger=f"goal:Ge(Pow(Symbol({var}), Number(2)), Number(0))",
                confidence=None,
                trace=list(goal.trace),
                name="Nonnegativity of square",
            )
        )

    if _match_sum_of_first_n_integers(goal.expr):
        out.append(
            Concept(
                id="sum_of_first_n_integers",
                role=ConceptRole.PATTERN,
                trigger="goal:Eq(Sum(k,1,n,k), n(n+1)/2)",
                confidence=None,
                trace=list(goal.trace),
                name="Arithmetic series sum",
            )
        )
    return out


def _match_assumption(assumption: Assumption, idx: int) -> list[Concept]:
    out: list[Concept] = []
    var = _match_nonnegativity_of_square(assumption.expr)
    if var is not None:
        out.append(
            Concept(
                id="nonnegativity_of_square",
                role=ConceptRole.PATTERN,
                trigger=f"assumption[{idx}]:Ge(Pow(Symbol({var}), Number(2)), Number(0))",
                confidence=None,
                trace=list(assumption.trace),
                name="Nonnegativity of square",
            )
        )

    if _match_sum_of_first_n_integers(assumption.expr):
        out.append(
            Concept(
                id="sum_of_first_n_integers",
                role=ConceptRole.PATTERN,
                trigger=f"assumption[{idx}]:Eq(Sum(k,1,n,k), n(n+1)/2)",
                confidence=None,
                trace=list(assumption.trace),
                name="Arithmetic series sum",
            )
        )

    pos_var = _match_positive_variable(assumption.expr)
    if pos_var is not None:
        out.append(
            Concept(
                id=f"positivity:{pos_var}",
                role=ConceptRole.DOMAIN,
                trigger=f"assumption[{idx}]:Gt(Symbol({pos_var}), Number(0))",
                confidence=None,
                trace=list(assumption.trace),
                name=f"Positive variable {pos_var}",
            )
        )
    return out


def extract_concepts(mvir: MVIR) -> list[Concept]:
    """Extract deterministic concepts from obvious goal/assumption expression patterns."""

    candidates: list[Concept] = []
    candidates.extend(_match_goal(mvir.goal))
    for idx, assumption in enumerate(mvir.assumptions):
        candidates.extend(_match_assumption(assumption, idx))

    by_id: dict[str, Concept] = {}
    for concept in candidates:
        if concept.id not in by_id:
            by_id[concept.id] = concept

    return sorted(by_id.values(), key=lambda item: item.id)


def augment_mvir_with_concepts(mvir: MVIR) -> MVIR:
    """Return a copy of MVIR with concepts deterministically replaced by extracted concepts."""

    return mvir.model_copy(update={"concepts": extract_concepts(mvir)})
