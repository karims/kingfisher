"""Pydantic models for MVIR payloads."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from mvir.core.ast import Expr


class EntityKind(str, Enum):
    """Entity category."""

    VARIABLE = "variable"
    CONSTANT = "constant"
    FUNCTION = "function"
    SET = "set"
    SEQUENCE = "sequence"
    POINT = "point"
    VECTOR = "vector"
    OBJECT = "object"


class AssumptionKind(str, Enum):
    """Assumption category."""

    GIVEN = "given"
    DERIVED = "derived"
    WLOG = "wlog"


class GoalKind(str, Enum):
    """Goal category."""

    PROVE = "prove"
    FIND = "find"
    COMPUTE = "compute"
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"
    EXISTS = "exists"
    COUNTEREXAMPLE = "counterexample"


class ConceptRole(str, Enum):
    """Concept usage role."""

    DOMAIN = "domain"
    PATTERN = "pattern"
    CANDIDATE_TOOL = "candidate_tool"
    DEFINITION = "definition"
    REPRESENTATION_HINT = "representation_hint"


class Meta(BaseModel):
    """Metadata for MVIR documents."""

    version: str = Field(pattern=r"^0\.1$")
    id: str = Field(min_length=1)
    generator: str | None = None
    created_at: str | None = None


class Source(BaseModel):
    """Source payload and annotations."""

    text: str
    normalized_text: str | None = None
    spans: list[dict] | None = None


class TraceSpan(BaseModel):
    """Span of source text referenced by traces."""

    span_id: str = Field(min_length=1)
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    text: str | None = None

    @model_validator(mode="after")
    def _validate_bounds(self) -> "TraceSpan":
        if self.end < self.start:
            raise ValueError("TraceSpan.end must be >= TraceSpan.start")
        return self


class Entity(BaseModel):
    """Named entity reference."""

    id: str = Field(min_length=1)
    kind: EntityKind
    type: str
    properties: list[str] = Field(default_factory=list)
    trace: list[str] = Field(default_factory=list)


class Assumption(BaseModel):
    """Assumption expression with provenance."""

    expr: Expr
    kind: AssumptionKind
    trace: list[str] = Field(default_factory=list)
    id: str | None = None

    @model_validator(mode="after")
    def _validate_id(self) -> "Assumption":
        if self.id is not None and not self.id:
            raise ValueError("Assumption.id must be a non-empty string")
        return self


class Goal(BaseModel):
    """Goal specification."""

    kind: GoalKind
    expr: Expr
    trace: list[str] = Field(default_factory=list)
    target: Expr | None = None

    @model_validator(mode="after")
    def _validate_find_target(self) -> "Goal":
        if self.kind == GoalKind.FIND and self.target is None:
            raise ValueError("Find goal requires a target.")
        return self


class Concept(BaseModel):
    """Concept or hint associated with the MVIR document."""

    id: str = Field(min_length=1)
    role: ConceptRole
    trigger: str | None = None
    confidence: float | None = None
    trace: list[str] = Field(default_factory=list)
    name: str | None = None


class Warning(BaseModel):
    """Non-fatal issues captured during extraction."""

    code: str
    message: str
    trace: list[str] = Field(default_factory=list)
    details: dict | None = None


class MVIR(BaseModel):
    """Top-level MVIR document."""

    meta: Meta
    source: Source
    entities: list[Entity]
    assumptions: list[Assumption]
    goal: Goal
    concepts: list[Concept] = Field(default_factory=list)
    warnings: list[Warning] = Field(default_factory=list)
    trace: list[TraceSpan] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_entity_ids(self) -> "MVIR":
        if not self.trace:
            raise ValueError("MVIR.trace must contain at least one TraceSpan")

        ids = [entity.id for entity in self.entities]
        if len(ids) != len(set(ids)):
            raise ValueError("Entity ids must be unique")

        trace_ids = {span.span_id for span in self.trace}
        referenced = set()
        for entity in self.entities:
            referenced.update(entity.trace)
        for assumption in self.assumptions:
            referenced.update(assumption.trace)
        referenced.update(self.goal.trace)
        for concept in self.concepts:
            referenced.update(concept.trace)
        for warning in self.warnings:
            referenced.update(warning.trace)

        missing = sorted(ref_id for ref_id in referenced if ref_id not in trace_ids)
        if missing:
            raise ValueError(f"Unknown trace ids referenced: {missing}")

        return self


def load_mvir(path: str) -> MVIR:
    """Load MVIR data from a JSON file."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return MVIR.model_validate(payload)


def dump_mvir(mvir: MVIR, path: str) -> None:
    """Write MVIR data to a JSON file."""

    payload = mvir.model_dump(by_alias=False, exclude_none=True)
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
