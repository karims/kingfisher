import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "examples" / "phase0_examples.json"
PROBLEMS_DIR = ROOT / "examples" / "problems"
EXPECTED_DIR = ROOT / "examples" / "expected"

def main():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    PROBLEMS_DIR.mkdir(parents=True, exist_ok=True)
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)

    for ex in data["examples"]:
        ex_id = ex["id"]
        text = ex["problem_text"]
        # Write problem text
        (PROBLEMS_DIR / f"{ex_id}.txt").write_text(text.strip() + "\n", encoding="utf-8")

        # Auto-build full-span trace offsets (Phase 0: one span covering whole text)
        trace = [{
            "span_id": "s0",
            "start": 0,
            "end": len(text),
            "text": text
        }]

        mvir = ex["expected_mvir"]
        # Ensure required fields
        mvir.setdefault("meta", {})
        mvir["meta"].setdefault("version", "0.1")
        mvir["meta"].setdefault("id", ex_id)
        mvir["meta"].setdefault("generator", "kingfisher-phase0")

        mvir.setdefault("source", {})
        mvir["source"]["text"] = text

        mvir["trace"] = trace

        # Ensure every listed item references s0 if trace missing
        def ensure_trace(obj):
            if isinstance(obj, dict):
                if "trace" in obj and not obj["trace"]:
                    obj["trace"] = ["s0"]
                for v in obj.values():
                    ensure_trace(v)
            elif isinstance(obj, list):
                for it in obj:
                    ensure_trace(it)

        ensure_trace(mvir)

        # Write expected JSON
        (EXPECTED_DIR / f"{ex_id}.json").write_text(
            json.dumps(mvir, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )

        # Write expected MD
        (EXPECTED_DIR / f"{ex_id}.md").write_text(ex["expected_md"].strip() + "\n", encoding="utf-8")

    print(f"Generated {len(data['examples'])} examples.")

if __name__ == "__main__":
    main()
