"""CLI scaffolding for Phase 4 directory formalization.

Batch execution may use optional network providers.
Offline tests should still pass without making network calls.
"""

from __future__ import annotations


def main(argv: list[str] | None = None) -> int:
    """Run directory-level formalization pipeline."""

    _ = argv
    raise NotImplementedError("Directory formalization CLI is deferred in Phase 4 scaffolding.")


if __name__ == "__main__":
    raise SystemExit(main())

