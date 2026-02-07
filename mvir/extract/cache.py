"""File-based response cache for extraction providers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone


class ResponseCache:
    """Small file-backed cache for raw provider outputs."""

    def __init__(self, cache_dir: str | Path = ".mvir_cache") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path_for_key(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> str | None:
        """Return cached value for key, or None if missing/unreadable."""

        path = self._path_for_key(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        value = payload.get("value")
        if isinstance(value, str):
            return value
        return None

    def set(self, key: str, value: str) -> None:
        """Persist cached response value."""

        payload = {
            "value": value,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._path_for_key(key).write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )

    def make_key(
        self,
        *,
        provider_name: str,
        model_name: str | None,
        temperature: float,
        max_tokens: int,
        prompt: str,
    ) -> str:
        """Build a deterministic cache key from request inputs."""

        stable_obj = {
            "provider_name": provider_name,
            "model_name": model_name or "",
            "temperature": temperature,
            "max_tokens": max_tokens,
            "prompt": prompt,
        }
        canonical = json.dumps(stable_obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
