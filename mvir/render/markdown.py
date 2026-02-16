"""Deterministic Markdown rendering for MVIR documents."""

from __future__ import annotations

from mvir.core.ast import (
    Add,
    Bool,
    Call,
    Div,
    Divides,
    Eq,
    Expr,
    Ge,
    Gt,
    Le,
    Lt,
    Mul,
    Neg,
    Neq,
    Number,
    Pow,
    Sum,
    Symbol,
)
from mvir.core.models import MVIR


_BINARY_OP_SYMBOLS = {
    "Eq": "=",
    "Neq": "!=",
    "Lt": "<",
    "Le": "<=",
    "Gt": ">",
    "Ge": ">=",
    "Divides": "|",
}


def _truncate_text(value: str | None, limit: int) -> str:
    text = value or ""
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3] + "..."


def _escape_cell(value: str | None) -> str:
    return (value or "").replace("\r", " ").replace("\n", " ").replace("|", "\\|")


def _is_atomic(expr: Expr) -> bool:
    return isinstance(expr, (Symbol, Number, Bool, Call))


def _render_add_arg(expr: Expr) -> str:
    text = render_expr(expr)
    if isinstance(expr, (Eq, Neq, Lt, Le, Gt, Ge, Divides)):
        return f"({text})"
    return text


def _render_mul_arg(expr: Expr) -> str:
    text = render_expr(expr)
    if isinstance(expr, (Add, Eq, Neq, Lt, Le, Gt, Ge, Divides)):
        return f"({text})"
    return text


def _render_pow_part(expr: Expr) -> str:
    text = render_expr(expr)
    if _is_atomic(expr):
        return text
    return f"({text})"


def render_expr(expr: Expr) -> str:
    """Render an MVIR expression into deterministic human-readable text."""

    if isinstance(expr, Symbol):
        return expr.id
    if isinstance(expr, Number):
        return str(expr.value)
    if isinstance(expr, Bool):
        return "true" if expr.value else "false"
    if isinstance(expr, Add):
        return " + ".join(_render_add_arg(arg) for arg in expr.args)
    if isinstance(expr, Mul):
        return " * ".join(_render_mul_arg(arg) for arg in expr.args)
    if isinstance(expr, Div):
        return f"({render_expr(expr.num)})/({render_expr(expr.den)})"
    if isinstance(expr, Pow):
        return f"{_render_pow_part(expr.base)}^{_render_pow_part(expr.exp)}"
    if isinstance(expr, Neg):
        return f"-({render_expr(expr.arg)})"
    if isinstance(expr, (Eq, Neq, Lt, Le, Gt, Ge, Divides)):
        op = _BINARY_OP_SYMBOLS[expr.node]
        return f"{render_expr(expr.lhs)} {op} {render_expr(expr.rhs)}"
    if isinstance(expr, Sum):
        return (
            f"sum_{{{expr.var}={render_expr(expr.from_)}..{render_expr(expr.to)}}} "
            f"({render_expr(expr.body)})"
        )
    if isinstance(expr, Call):
        args = ", ".join(render_expr(arg) for arg in expr.args)
        return f"{expr.fn}({args})"

    return expr.__class__.__name__


def _render_trace_ids(trace_ids: list[str]) -> str:
    return ", ".join(trace_ids)


def render_mvir_markdown(mvir: MVIR) -> str:
    """Render an MVIR document as a deterministic Markdown report."""

    lines: list[str] = []
    lines.append(f"# MVIR Report: {mvir.meta.id}")

    lines.append("")
    lines.append("## Meta")
    lines.append(f"- version: {mvir.meta.version}")
    lines.append(f"- id: {mvir.meta.id}")
    lines.append(f"- generator: {mvir.meta.generator or ''}")
    lines.append(f"- created_at: {mvir.meta.created_at or ''}")

    source_preview = _truncate_text(mvir.source.text, 300)
    lines.append("")
    lines.append("## Source")
    lines.append(f"- preview: {_escape_cell(source_preview)}")
    lines.append(f"- length: {len(mvir.source.text)}")

    lines.append("")
    lines.append("## Trace Spans")
    lines.append("| span_id | start | end | text |")
    lines.append("| --- | --- | --- | --- |")
    for span in mvir.trace:
        text = _truncate_text(span.text, 120)
        lines.append(
            f"| {_escape_cell(span.span_id)} | {span.start} | {span.end} | {_escape_cell(text)} |"
        )

    lines.append("")
    lines.append("## Entities")
    lines.append("| id | kind | type | properties | trace_ids |")
    lines.append("| --- | --- | --- | --- | --- |")
    for entity in sorted(mvir.entities, key=lambda item: item.id):
        properties = ", ".join(entity.properties)
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_cell(entity.id),
                    _escape_cell(entity.kind.value),
                    _escape_cell(entity.type),
                    _escape_cell(properties),
                    _escape_cell(_render_trace_ids(entity.trace)),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Assumptions")
    for assumption in mvir.assumptions:
        rendered = render_expr(assumption.expr)
        id_suffix = f"; id: {assumption.id}" if assumption.id else ""
        lines.append(
            f"- [{assumption.kind.value}] {rendered} "
            f"(trace: {_render_trace_ids(assumption.trace)}{id_suffix})"
        )

    lines.append("")
    lines.append("## Goal")
    lines.append(f"- {mvir.goal.kind.value}: {render_expr(mvir.goal.expr)}")
    if mvir.goal.target is not None:
        lines.append(f"- target: {render_expr(mvir.goal.target)}")

    lines.append("")
    lines.append("## Concepts")
    lines.append("| id | role | name | trigger | confidence | trace_ids |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for concept in sorted(mvir.concepts, key=lambda item: (item.role.value, item.id)):
        confidence = "" if concept.confidence is None else str(concept.confidence)
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_cell(concept.id),
                    _escape_cell(concept.role.value),
                    _escape_cell(concept.name),
                    _escape_cell(concept.trigger),
                    _escape_cell(confidence),
                    _escape_cell(_render_trace_ids(concept.trace)),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Warnings")
    for warning in sorted(mvir.warnings, key=lambda item: item.code):
        lines.append(
            f"- {warning.code}: {warning.message} "
            f"(trace: {_render_trace_ids(warning.trace)})"
        )

    return "\n".join(lines) + "\n"
