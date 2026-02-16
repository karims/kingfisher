"""Append-only JSONL trace logger."""

from __future__ import annotations

import json
from pathlib import Path


class TraceLogger:
    """Append-only JSONL logger for solver/pipeline trace events."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a", encoding="utf-8")

    def append(self, event: dict) -> None:
        """Append one compact JSON event line."""

        line = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
        self._fh.write(line + "\n")

    def flush(self) -> None:
        """Flush pending writes to disk."""

        self._fh.flush()

    def close(self) -> None:
        """Close the underlying file handle."""

        self._fh.close()
