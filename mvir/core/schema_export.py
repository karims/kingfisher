"""Schema export utilities for MVIR."""

from __future__ import annotations

import json
from pathlib import Path

from mvir.core.models import MVIR


def export_schema(out_path: str = "schemas/mvir_0_1.json") -> None:
    """Export MVIR JSON schema to the given path."""

    schema = MVIR.model_json_schema()
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, indent=2), encoding="utf-8")


def main() -> None:
    """CLI entrypoint for schema export."""

    export_schema()


if __name__ == "__main__":
    main()
