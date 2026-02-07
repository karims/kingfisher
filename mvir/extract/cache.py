"""Cache scaffolding for Phase 4 extraction pipeline.

Caching is allowed only as a recomputation skip mechanism.
Cache behavior must not alter MVIR content.
"""

from __future__ import annotations

from pathlib import Path

from mvir.core.models import MVIR


def cache_key_for_text(problem_id: str, text: str, provider_name: str, model: str) -> str:
    """Build a deterministic cache key for a formalization request."""

    _ = problem_id
    _ = text
    _ = provider_name
    _ = model
    raise NotImplementedError("Cache key implementation is deferred in Phase 4 scaffolding.")


def load_cached_mvir(cache_dir: Path, key: str) -> MVIR | None:
    """Load an MVIR document from cache if present."""

    _ = cache_dir
    _ = key
    raise NotImplementedError("Cache load implementation is deferred in Phase 4 scaffolding.")


def save_cached_mvir(cache_dir: Path, key: str, mvir: MVIR) -> Path:
    """Persist an MVIR document to cache and return the cache path."""

    _ = cache_dir
    _ = key
    _ = mvir
    raise NotImplementedError("Cache write implementation is deferred in Phase 4 scaffolding.")

