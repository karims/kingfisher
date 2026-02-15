"""Run golden regression problems through MVIR extraction/validation."""

from __future__ import annotations

import json
import os
import sys
from argparse import ArgumentParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mvir.core.models import MVIR
from mvir.extract.contract import validate_grounding_contract
from mvir.extract.formalize import formalize_text_to_mvir
from mvir.extract.providers.openai_provider import OpenAIProvider
from mvir.preprocess.context import build_preprocess_output

SNAPSHOT_PATH = ROOT / "examples" / "problems" / "golden" / "snapshots.json"
OUT_DIR = ROOT / "out" / "mvir"
MODES = ("json_schema", "json_object")


def _load_offline_fixture(root: Path) -> dict[str, str]:
    fixture_path = root / "examples" / "mock_llm" / "mock_responses.json"
    if not fixture_path.exists():
        return {}
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _stable_snapshot(mvir: MVIR) -> dict:
    entities = [
        {
            "id": entity.id,
            "kind": getattr(entity.kind, "value", entity.kind),
            "type": entity.type,
        }
        for entity in mvir.entities
    ]
    assumptions_kind = [getattr(a.kind, "value", a.kind) for a in mvir.assumptions]
    trace = [
        {
            "span_id": span.span_id,
            "start": span.start,
            "end": span.end,
            "text": span.text,
        }
        for span in mvir.trace
    ]
    return {
        "meta": {"version": mvir.meta.version, "id": mvir.meta.id},
        "entities": entities,
        "assumptions_kind": assumptions_kind,
        "goal_kind": getattr(mvir.goal.kind, "value", mvir.goal.kind),
        "trace": trace,
    }


def _provider_for_mode(mode: str) -> OpenAIProvider:
    if mode == "json_schema":
        return OpenAIProvider(format_mode="json_schema", allow_fallback=False)
    if mode == "json_object":
        return OpenAIProvider(format_mode="json_object", allow_fallback=True)
    raise ValueError(f"Unknown mode: {mode}")


def main(argv: list[str] | None = None) -> int:
    parser = ArgumentParser(description="Run golden extraction regression in multiple modes.")
    parser.add_argument(
        "--update-goldens",
        action="store_true",
        help="Refresh snapshot file with current stable fields.",
    )
    args = parser.parse_args(argv)

    root = ROOT
    golden_dir = root / "examples" / "problems" / "golden"
    files = sorted(golden_dir.rglob("*.txt"))

    offline_mode = os.getenv("MVIR_OFFLINE") == "1" or not os.getenv("OPENAI_API_KEY")
    mapping = _load_offline_fixture(root) if offline_mode else {}
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    snapshots: dict = {}
    if SNAPSHOT_PATH.exists():
        loaded = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            snapshots = loaded

    current: dict[str, dict[str, dict]] = {mode: {} for mode in MODES}
    failed: list[str] = []
    total = len(files) * len(MODES)

    for mode in MODES:
        provider = None if offline_mode else _provider_for_mode(mode)
        for path in files:
            problem_id = path.stem
            text = path.read_text(encoding="utf-8")
            _ = build_preprocess_output(text)
            key = f"{problem_id}.{mode}"
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

                (OUT_DIR / f"{problem_id}.{mode}.json").write_text(
                    json.dumps(mvir.model_dump(by_alias=False, exclude_none=True), indent=2),
                    encoding="utf-8",
                )
                current[mode][problem_id] = _stable_snapshot(mvir)

                if not args.update_goldens:
                    expected_mode = snapshots.get(mode, {})
                    expected = expected_mode.get(problem_id) if isinstance(expected_mode, dict) else None
                    if expected is None:
                        failed.append(f"{key} (missing snapshot)")
                    elif expected != current[mode][problem_id]:
                        failed.append(f"{key} (snapshot mismatch)")
            except Exception:
                failed.append(str(path.relative_to(golden_dir)) + f" [{mode}]")

    if args.update_goldens:
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(
            json.dumps(current, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

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
