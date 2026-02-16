"""Operator registry for mapping surface forms to canonical MVIR operator specs."""

from __future__ import annotations

from dataclasses import dataclass


def _normalize_surface(surface: str) -> str:
    return " ".join(surface.strip().lower().split())


@dataclass(frozen=True, slots=True)
class OperatorSpec:
    """Canonical operator metadata used by parsing/normalization layers."""

    canonical_id: str
    ast_node: str
    surface_forms: tuple[str, ...]
    arity: int | None
    argument_roles: tuple[str, ...]
    emit_call_fn: str | None = None


class OperatorRegistry:
    """Deterministic lookup table for operator surface forms and AST nodes."""

    def __init__(self, specs: list[OperatorSpec]) -> None:
        self._specs: tuple[OperatorSpec, ...] = tuple(specs)
        self._by_surface: dict[str, OperatorSpec] = {}
        self._by_node: dict[str, OperatorSpec] = {}

        for spec in self._specs:
            if spec.ast_node not in self._by_node:
                self._by_node[spec.ast_node] = spec
            for surface in spec.surface_forms:
                normalized = _normalize_surface(surface)
                if normalized and normalized not in self._by_surface:
                    self._by_surface[normalized] = spec

    def lookup(self, surface: str) -> OperatorSpec | None:
        """Lookup operator spec by surface token/alias."""

        return self._by_surface.get(_normalize_surface(surface))

    def canonical(self, node: str) -> OperatorSpec | None:
        """Lookup operator spec by canonical AST node name (e.g. \"Lt\")."""

        return self._by_node.get(node)

    def all_nodes(self) -> set[str]:
        """Return all AST node names represented by this registry."""

        return set(self._by_node.keys())


DEFAULT_REGISTRY = OperatorRegistry(
    [
        OperatorSpec(
            canonical_id="add",
            ast_node="Add",
            surface_forms=("+", "plus", "add", "sum"),
            arity=None,
            argument_roles=("args",),
        ),
        OperatorSpec(
            canonical_id="mul",
            ast_node="Mul",
            surface_forms=("*", "times", "multiply", "product", "×", r"\cdot", r"\times"),
            arity=None,
            argument_roles=("args",),
        ),
        OperatorSpec(
            canonical_id="div",
            ast_node="Div",
            surface_forms=("/", "divide", "division", "÷", r"\frac", "over"),
            arity=2,
            argument_roles=("num", "den"),
        ),
        OperatorSpec(
            canonical_id="pow",
            ast_node="Pow",
            surface_forms=("^", "**", "power", "to the power"),
            arity=2,
            argument_roles=("base", "exp"),
        ),
        OperatorSpec(
            canonical_id="neg",
            ast_node="Neg",
            surface_forms=("-", "negative", "unary minus"),
            arity=1,
            argument_roles=("arg",),
        ),
        OperatorSpec(
            canonical_id="eq",
            ast_node="Eq",
            surface_forms=("=", "==", "equals", "equal"),
            arity=2,
            argument_roles=("lhs", "rhs"),
        ),
        OperatorSpec(
            canonical_id="neq",
            ast_node="Neq",
            surface_forms=("!=", "≠", r"\neq", "not equal"),
            arity=2,
            argument_roles=("lhs", "rhs"),
        ),
        OperatorSpec(
            canonical_id="lt",
            ast_node="Lt",
            surface_forms=("<", "less than", r"\lt"),
            arity=2,
            argument_roles=("lhs", "rhs"),
        ),
        OperatorSpec(
            canonical_id="le",
            ast_node="Le",
            surface_forms=("<=", "≤", r"\le", r"\leq", "at most"),
            arity=2,
            argument_roles=("lhs", "rhs"),
        ),
        OperatorSpec(
            canonical_id="gt",
            ast_node="Gt",
            surface_forms=(">", "greater than", r"\gt"),
            arity=2,
            argument_roles=("lhs", "rhs"),
        ),
        OperatorSpec(
            canonical_id="ge",
            ast_node="Ge",
            surface_forms=(">=", "≥", r"\ge", r"\geq", "at least"),
            arity=2,
            argument_roles=("lhs", "rhs"),
        ),
        OperatorSpec(
            canonical_id="divides",
            ast_node="Divides",
            surface_forms=("divides", "|", r"\mid"),
            arity=2,
            argument_roles=("lhs", "rhs"),
        ),
        OperatorSpec(
            canonical_id="sum",
            ast_node="Sum",
            surface_forms=("sum", "summation", "∑", r"\sum"),
            arity=4,
            argument_roles=("var", "from", "to", "body"),
        ),
        OperatorSpec(
            canonical_id="call",
            ast_node="Call",
            surface_forms=("call", "function", "apply"),
            arity=None,
            argument_roles=("fn", "args"),
        ),
        # Future-facing example: set intersection currently represented as Call(fn="intersection", ...).
        OperatorSpec(
            canonical_id="set_intersection",
            ast_node="Call",
            surface_forms=(r"\cap", "∩", "intersection"),
            arity=None,
            argument_roles=("args",),
            emit_call_fn="intersection",
        ),
        # Future-facing example: integral currently represented as Call(fn="integral", ...).
        OperatorSpec(
            canonical_id="integral",
            ast_node="Call",
            surface_forms=(r"\int", "∫", "integral"),
            arity=None,
            argument_roles=("args",),
            emit_call_fn="integral",
        ),
    ]
)

