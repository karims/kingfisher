"""Trace event helper utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def _utc_iso_z_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def new_event(
    kind: str,
    message: str,
    *,
    data: dict | None = None,
    trace: list[str] | None = None,
    refs: list[str] | None = None,
) -> dict:
    """Create a new trace event dict with id and UTC timestamp."""

    return {
        "event_id": uuid4().hex,
        "ts": _utc_iso_z_now(),
        "kind": kind,
        "message": message,
        "data": data,
        "trace": trace,
        "refs": refs,
    }
