"""Deterministic sanitizer for near-valid MVIR payloads."""

from __future__ import annotations

from copy import deepcopy


_ENTITY_KINDS = {
    "variable",
    "constant",
    "function",
    "set",
    "sequence",
    "point",
    "vector",
    "object",
}
_ASSUMPTION_KIND_MAP = {
    "assumption": "given",
    "given_assumption": "given",
    "hypothesis": "given",
}
_CONCEPT_ROLE_MAP = {
    "theorem": "definition",
    "formula": "definition",
    "concept": "pattern",
}


def sanitize_mvir_payload(payload: dict) -> dict:
    """Sanitize common schema-contract issues without inventing trace spans/ids."""

    data = deepcopy(payload)
    if not isinstance(data, dict):
        return data

    data.setdefault("concepts", [])
    data.setdefault("warnings", [])
    data.setdefault("entities", [])
    data.setdefault("assumptions", [])
    data.setdefault("trace", [])

    meta = data.get("meta")
    if isinstance(meta, dict):
        meta.setdefault("generator", None)
        meta.setdefault("created_at", None)

    source = data.get("source")
    if isinstance(source, dict):
        source.setdefault("normalized_text", None)
        source.setdefault("spans", None)

    entities = data.get("entities")
    if isinstance(entities, list):
        for entity in entities:
            if not isinstance(entity, dict):
                continue
            entity.setdefault("properties", [])
            entity.setdefault("trace", [])
            entity_type = entity.get("type")
            if not isinstance(entity_type, str) or not entity_type.strip():
                entity["type"] = "Unknown"
            kind = entity.get("kind")
            if isinstance(kind, str):
                kind_lower = kind.lower()
                if kind_lower in _ENTITY_KINDS:
                    entity["kind"] = kind_lower

    assumptions = data.get("assumptions")
    if isinstance(assumptions, list):
        for assumption in assumptions:
            if not isinstance(assumption, dict):
                continue
            assumption.setdefault("trace", [])
            assumption.setdefault("id", None)
            if "kind" not in assumption:
                assumption["kind"] = "given"
            kind = assumption.get("kind")
            if isinstance(kind, str):
                kind_lower = kind.lower()
                if kind_lower in _ASSUMPTION_KIND_MAP:
                    assumption["kind"] = _ASSUMPTION_KIND_MAP[kind_lower]
                elif kind_lower in {"given", "derived", "wlog"}:
                    assumption["kind"] = kind_lower

    original_goal = data.get("goal")
    kept_goal = original_goal
    had_multiple_goals = False
    if isinstance(original_goal, list):
        had_multiple_goals = len(original_goal) > 1
        kept_goal = original_goal[0] if original_goal else {}
        data["goal"] = kept_goal
    if isinstance(data.get("goal"), dict):
        goal = data["goal"]
        if "kind" not in goal:
            goal["kind"] = "prove"
        kind = goal.get("kind")
        if isinstance(kind, str):
            kind_lower = kind.lower()
            if kind_lower == "goal":
                goal["kind"] = "prove"
            elif kind_lower in {
                "prove",
                "find",
                "compute",
                "maximize",
                "minimize",
                "exists",
                "counterexample",
            }:
                goal["kind"] = kind_lower
        goal.setdefault("trace", [])
        goal.setdefault("target", None)

    concepts = data.get("concepts")
    if isinstance(concepts, list):
        for concept in concepts:
            if not isinstance(concept, dict):
                continue
            concept.setdefault("trace", [])
            if "role" not in concept:
                concept["role"] = "definition"
            role = concept.get("role")
            if isinstance(role, str):
                role_lower = role.lower()
                if role_lower in _CONCEPT_ROLE_MAP:
                    concept["role"] = _CONCEPT_ROLE_MAP[role_lower]
                elif role_lower in {
                    "domain",
                    "pattern",
                    "candidate_tool",
                    "definition",
                    "representation_hint",
                }:
                    concept["role"] = role_lower
            concept.setdefault("trigger", None)
            concept.setdefault("confidence", None)
            concept.setdefault("name", None)

    warnings = data.get("warnings")
    if isinstance(warnings, list):
        for warning in warnings:
            if not isinstance(warning, dict):
                continue
            warning.setdefault("trace", [])
            warning.setdefault("details", None)
            if "code" not in warning:
                warning["code"] = "unspecified"

    if had_multiple_goals:
        goal_trace: list[str] = []
        if isinstance(data.get("goal"), dict):
            trace = data["goal"].get("trace")
            if isinstance(trace, list):
                goal_trace = [t for t in trace if isinstance(t, str)]
        warnings_list = data.get("warnings")
        if not isinstance(warnings_list, list):
            warnings_list = []
            data["warnings"] = warnings_list
        warnings_list.append(
            {
                "code": "multiple_goals",
                "message": "Multiple goals returned; kept the first goal only.",
                "trace": goal_trace,
                "details": None,
            }
        )

    return data

