"""Batch reporting scaffolding for Phase 4 extraction runs.

Reports summarize pipeline outcomes without changing MVIR schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class FormalizeItemReport:
    """Per-problem report entry for directory formalization."""

    problem_id: str
    status: str
    output_path: str | None = None
    error: str | None = None
    cache_hit: bool = False


@dataclass(frozen=True)
class FormalizeBatchReport:
    """Aggregate report for a directory formalization run."""

    items: list[FormalizeItemReport] = field(default_factory=list)


def write_batch_report(report: FormalizeBatchReport, path: Path) -> Path:
    """Write a batch report to disk and return output path."""

    _ = report
    _ = path
    raise NotImplementedError("Batch report serialization is deferred in Phase 4 scaffolding.")

