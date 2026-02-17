"""Deterministic trace graph export from MVIR and optional trace events."""

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


def iter_symbol_ids(expr: Expr):
    """Yield Symbol.id values appearing in an expression tree."""

    if isinstance(expr, Symbol):
        yield expr.id
        return
    if isinstance(expr, (Number, Bool)):
        return
    if isinstance(expr, (Add, Mul)):
        for arg in expr.args:
            yield from iter_symbol_ids(arg)
        return
    if isinstance(expr, Div):
        yield from iter_symbol_ids(expr.num)
        yield from iter_symbol_ids(expr.den)
        return
    if isinstance(expr, Pow):
        yield from iter_symbol_ids(expr.base)
        yield from iter_symbol_ids(expr.exp)
        return
    if isinstance(expr, Neg):
        yield from iter_symbol_ids(expr.arg)
        return
    if isinstance(expr, (Eq, Neq, Lt, Le, Gt, Ge, Divides)):
        yield from iter_symbol_ids(expr.lhs)
        yield from iter_symbol_ids(expr.rhs)
        return
    if isinstance(expr, Sum):
        yield from iter_symbol_ids(expr.from_)
        yield from iter_symbol_ids(expr.to)
        yield from iter_symbol_ids(expr.body)
        return
    if isinstance(expr, Call):
        for arg in expr.args:
            yield from iter_symbol_ids(arg)


def _event_id(event: dict, idx: int) -> str:
    event_id = event.get("event_id")
    if isinstance(event_id, str) and event_id:
        return f"trace_event:{event_id}"
    return f"trace_event:{idx:04d}"


def build_trace_graph(mvir: MVIR, solver_trace: list[dict] | None = None) -> dict:
    """Build a deterministic node/edge graph from MVIR and optional trace events."""

    nodes: list[dict] = []
    edges: list[dict] = []

    goal_node_id = "goal"
    nodes.append(
        {
            "id": goal_node_id,
            "type": "goal",
            "label": f"goal:{mvir.goal.kind.value}",
            "data": {"kind": mvir.goal.kind.value, "trace": list(mvir.goal.trace)},
        }
    )

    node_trace_refs: dict[str, set[str]] = {goal_node_id: set(mvir.goal.trace)}

    entity_node_ids: dict[str, str] = {}
    for entity in mvir.entities:
        node_id = f"entity:{entity.id}"
        entity_node_ids[entity.id] = node_id
        nodes.append(
            {
                "id": node_id,
                "type": "entity",
                "label": entity.id,
                "data": {
                    "kind": entity.kind.value,
                    "type": entity.type,
                    "trace": list(entity.trace),
                },
            }
        )
        node_trace_refs[node_id] = set(entity.trace)

    assumption_node_ids: list[str] = []
    assumption_symbols: list[set[str]] = []
    for idx, assumption in enumerate(mvir.assumptions):
        node_id = f"assumption:{idx:04d}"
        assumption_node_ids.append(node_id)
        symbols = set(iter_symbol_ids(assumption.expr))
        assumption_symbols.append(symbols)
        nodes.append(
            {
                "id": node_id,
                "type": "assumption",
                "label": assumption.id or f"assumption:{idx + 1}",
                "data": {
                    "kind": assumption.kind.value,
                    "trace": list(assumption.trace),
                    "assumption_id": assumption.id,
                },
            }
        )
        node_trace_refs[node_id] = set(assumption.trace)

    goal_symbols = set(iter_symbol_ids(mvir.goal.expr))
    for entity_id, entity_node_id in entity_node_ids.items():
        if entity_id in goal_symbols:
            edges.append(
                {
                    "src": entity_node_id,
                    "dst": goal_node_id,
                    "type": "mentions",
                    "data": {"symbol_id": entity_id},
                }
            )

    for entity_id, entity_node_id in entity_node_ids.items():
        for idx, assumption_node_id in enumerate(assumption_node_ids):
            if entity_id in assumption_symbols[idx]:
                edges.append(
                    {
                        "src": entity_node_id,
                        "dst": assumption_node_id,
                        "type": "mentions",
                        "data": {"symbol_id": entity_id},
                    }
                )

    for concept in mvir.concepts:
        node_id = f"concept:{concept.id}"
        concept_trace = set(concept.trace)
        nodes.append(
            {
                "id": node_id,
                "type": "concept",
                "label": concept.id,
                "data": {
                    "role": concept.role.value,
                    "trace": list(concept.trace),
                    "trigger": concept.trigger,
                    "name": concept.name,
                },
            }
        )
        node_trace_refs[node_id] = concept_trace

        if concept_trace.intersection(node_trace_refs[goal_node_id]):
            edges.append(
                {
                    "src": node_id,
                    "dst": goal_node_id,
                    "type": "trace_overlap",
                    "data": {
                        "shared_refs": sorted(
                            concept_trace.intersection(node_trace_refs[goal_node_id])
                        )
                    },
                }
            )

        for assumption_node_id in assumption_node_ids:
            shared = concept_trace.intersection(node_trace_refs[assumption_node_id])
            if shared:
                edges.append(
                    {
                        "src": node_id,
                        "dst": assumption_node_id,
                        "type": "trace_overlap",
                        "data": {"shared_refs": sorted(shared)},
                    }
                )

    if solver_trace is not None:
        events = solver_trace
    elif mvir.solver_trace is not None:
        events = [event.model_dump(exclude_none=True) for event in mvir.solver_trace.events]
    else:
        events = []
    for idx, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        node_id = _event_id(event, idx)
        refs = event.get("refs")
        refs_set = {ref for ref in refs if isinstance(ref, str)} if isinstance(refs, list) else set()

        nodes.append(
            {
                "id": node_id,
                "type": "trace_event",
                "label": event.get("kind") if isinstance(event.get("kind"), str) else "event",
                "data": {
                    "event_id": event.get("event_id"),
                    "kind": event.get("kind"),
                    "message": event.get("message"),
                    "data": event.get("data"),
                    "trace": event.get("trace"),
                    "refs": sorted(refs_set),
                },
            }
        )

        event_data = event.get("data")
        if isinstance(event_data, dict):
            mvir_id = event_data.get("mvir_id")
            problem_id = event_data.get("problem_id")
            if mvir_id == mvir.meta.id or problem_id == mvir.meta.id:
                edges.append(
                    {
                        "src": node_id,
                        "dst": goal_node_id,
                        "type": "produces",
                        "data": {"matched_id": mvir.meta.id},
                    }
                )

        if refs_set:
            for target_node_id, target_refs in node_trace_refs.items():
                shared = refs_set.intersection(target_refs)
                if shared:
                    edges.append(
                        {
                            "src": node_id,
                            "dst": target_node_id,
                            "type": "ref_overlap",
                            "data": {"shared_refs": sorted(shared)},
                        }
                    )

    nodes = sorted(nodes, key=lambda item: (item["type"], item["id"]))
    edges = sorted(edges, key=lambda item: (item["type"], item["src"], item["dst"]))

    return {
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "mvir_id": mvir.meta.id,
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
    }
