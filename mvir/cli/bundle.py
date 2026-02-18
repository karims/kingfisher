"""Export solver bundle JSON from MVIR JSON."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from mvir.core.models import MVIR
from mvir.solve.bundle import build_solver_bundle


def main(argv: list[str] | None = None) -> int:
    """Run the bundle export CLI."""

    parser = argparse.ArgumentParser(description="Export solver bundle from MVIR JSON.")
    parser.add_argument("path", help="Path to MVIR JSON file.")
    parser.add_argument("--out", required=True, help="Output bundle JSON path.")
    args = parser.parse_args(argv)

    try:
        in_path = Path(args.path)
        out_path = Path(args.out)

        payload = json.loads(in_path.read_text(encoding="utf-8"))
        mvir = MVIR.model_validate(payload)
        bundle = build_solver_bundle(mvir)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(asdict(bundle), ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        print(f"OK: {mvir.meta.id} -> {out_path}")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
