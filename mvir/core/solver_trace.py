"""Structured solver-trace models for MVIR representation logging."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SolverEventKind(str, Enum):
    """Enumerated solver-trace event kinds."""

    PLAN = "plan"
    CLAIM = "claim"
    TRANSFORM = "transform"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    BRANCH = "branch"
    BACKTRACK = "backtrack"
    FINAL = "final"
    NOTE = "note"
    ERROR = "error"


class SolverEvent(BaseModel):
    """Single event in a solver trace."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1)
    ts: str | None = None
    kind: SolverEventKind
    message: str
    data: dict | None = None
    trace: list[str] | None = None
    refs: list[str] | None = None


class SolverTrace(BaseModel):
    """Structured solver trace attached to an MVIR payload."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["0.1"] = "0.1"
    events: list[SolverEvent] = Field(default_factory=list)
    summary: str | None = None
    metrics: dict[str, float | int | str | bool] | None = None
    artifacts: dict[str, str] | None = None
