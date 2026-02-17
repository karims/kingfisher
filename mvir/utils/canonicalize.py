"""Deterministic canonical ordering helpers for MVIR outputs."""

from __future__ import annotations

import json

from mvir.core.models import MVIR


def _expr_sort_string(expr_payload: object) -> str:
    if isinstance(expr_payload, dict):
        return json.dumps(expr_payload, sort_keys=True, separators=(",", ":"))
    return json.dumps(expr_payload, sort_keys=True, separators=(",", ":"))


def _assumption_sort_key(item: dict) -> tuple[str, str]:
    trace = item.get("trace")
    first_trace = ""
    if isinstance(trace, list) and trace and isinstance(trace[0], str):
        first_trace = trace[0]
    expr_key = _expr_sort_string(item.get("expr"))
    return (first_trace, expr_key)


def canonicalize_mvir(mvir: MVIR) -> MVIR:
    """Return a new MVIR instance with deterministic list ordering."""

    payload = mvir.model_dump(by_alias=False, exclude_none=True)

    entities = payload.get("entities")
    if isinstance(entities, list):
        payload["entities"] = sorted(
            [item for item in entities if isinstance(item, dict)],
            key=lambda item: str(item.get("id", "")),
        )

    assumptions = payload.get("assumptions")
    if isinstance(assumptions, list):
        payload["assumptions"] = sorted(
            [item for item in assumptions if isinstance(item, dict)],
            key=_assumption_sort_key,
        )

    concepts = payload.get("concepts")
    if isinstance(concepts, list):
        payload["concepts"] = sorted(
            [item for item in concepts if isinstance(item, dict)],
            key=lambda item: str(item.get("id", "")),
        )

    warnings = payload.get("warnings")
    if isinstance(warnings, list):
        payload["warnings"] = sorted(
            [item for item in warnings if isinstance(item, dict)],
            key=lambda item: (str(item.get("code", "")), str(item.get("message", ""))),
        )

    return MVIR.model_validate(payload)
