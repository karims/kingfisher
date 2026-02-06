"""Tests for MVIR schema export."""

from __future__ import annotations

import json
from pathlib import Path

from mvir.core.schema_export import export_schema


def test_export_schema(tmp_path: Path) -> None:
    out_path = tmp_path / "mvir_0_1.json"
    export_schema(str(out_path))

    assert out_path.exists()
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert "properties" in payload
    assert "meta" in payload["properties"]
