"""Run golden regression problems through MVIR extraction/validation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mvir.core.models import MVIR
from mvir.extract.contract import validate_grounding_contract
from mvir.extract.formalize import formalize_text_to_mvir
from mvir.extract.providers.openai_provider import OpenAIProvider
from mvir.preprocess.context import build_preprocess_output


def _load_offline_fixture(root: Path) -> dict[str, str]:
    fixture_path = root / "examples" / "mock_llm" / "mock_responses.json"
    if not fixture_path.exists():
        return {}
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    root = ROOT
    golden_dir = root / "examples" / "problems" / "golden"
    files = sorted(golden_dir.rglob("*.txt"))

    offline_mode = os.getenv("MVIR_OFFLINE") == "1" or not os.getenv("OPENAI_API_KEY")
    mapping = _load_offline_fixture(root) if offline_mode else {}
    provider = OpenAIProvider(allow_fallback=True) if not offline_mode else None

    failed: list[str] = []
    for path in files:
        problem_id = path.stem
        text = path.read_text(encoding="utf-8")
        _ = build_preprocess_output(text)
        try:
            if offline_mode:
                if problem_id not in mapping:
                    raise ValueError(f"Missing offline fixture for problem_id '{problem_id}'")
                raw = mapping[problem_id]
                if not isinstance(raw, str):
                    raise ValueError(f"Offline fixture for '{problem_id}' is not a JSON string")
                payload = json.loads(raw)
                mvir = MVIR.model_validate(payload)
            else:
                assert provider is not None
                mvir = formalize_text_to_mvir(
                    text,
                    provider,
                    problem_id=problem_id,
                    temperature=0.0,
                    strict=True,
                )

            errors = validate_grounding_contract(mvir)
            if errors:
                raise ValueError("; ".join(errors))
        except Exception:
            failed.append(str(path.relative_to(golden_dir)))

    total = len(files)
    passed = total - len(failed)
    print(f"total={total} passed={passed} failed={len(failed)}")
    if failed:
        print("failed files:")
        for name in failed:
            print(name)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
