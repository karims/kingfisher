# Kingfisher Quickstart (Phase 3–4)

This quickstart shows how to verify the full Kingfisher pipeline end-to-end **without any network calls**, using the built-in Mock provider.

You will run:
1. Preprocess (lossless span splitting + offsets)
2. Formalize a single problem (offline)
3. Formalize a directory (batch mode)
4. Inspect outputs and the run report
5. Run the full test suite

This takes ~5–10 minutes for a new user.

---

## Prerequisites

- Python 3.10+ (recommended)
- Git
- A virtual environment

From the repository root:

### Windows (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
````

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## 1) Preprocess a problem (span splitting + offsets)

This step is **fully deterministic**.
It does **not** infer meaning or semantics.

```bash
python -m mvir.cli.preprocess examples/problems/latex_smoke_01.txt
```

Expected output (JSON):

* `text`: full original problem text
* `sentences`: list of sentence spans

  * `span_id` (s1, s2, …)
  * `start`, `end` character offsets
  * `text` slice exactly as in the source

Offsets are critical: all later MVIR extraction must reference these spans exactly.

---

## 2) Formalize a single problem (offline, Mock provider)

This runs the full Phase-3 extraction pipeline:

preprocess → prompt context → provider output →
MVIR schema validation → grounding contract validation

```bash
python -m mvir.cli.formalize examples/problems/latex_smoke_01.txt \
  --provider mock \
  --mock-path examples/mock_llm/mock_responses.json \
  --print
```

Expected behavior:

* MVIR JSON printed to stdout
* Final line:

  ```
  OK: latex_smoke_01
  ```

To write the MVIR to a file instead:

```bash
python -m mvir.cli.formalize examples/problems/latex_smoke_01.txt \
  --provider mock \
  --mock-path examples/mock_llm/mock_responses.json \
  --out out/latex_smoke_01.json
```

---

## 3) Formalize a directory (batch mode, offline)

This runs the same pipeline over **all `.txt` files** under a directory.

It produces:

* One MVIR JSON file per successful problem
* A run report summarizing successes and failures

```bash
python -m mvir.cli.formalize_dir examples/problems \
  --provider mock \
  --mock-path examples/mock_llm/mock_responses.json \
  --out-dir out/mvir \
  --report out/report.json
```

Example summary:

```text
total=8 ok=3 failed=5
top failure kinds:
- provider: 5
```

Meaning:

* 8 problem files were found
* 3 had mock responses available and succeeded
* 5 failed because the Mock provider had no response for them

This is expected unless you add more mock entries.

---

## 4) Inspect the run report

Open the generated report:

```bash
cat out/report.json
```

Structure:

* `ok`: list of problem IDs that succeeded
* `failed`: list of failure objects with:

  * `id`
  * `kind` (failure category)
  * `message` (human-readable explanation)

Example failure (offline mock mode):

* `kind: "provider"`
* Message indicates:

  * unknown `PROBLEM_ID`
  * available keys in the mock mapping

Failures are explicit and non-fatal by design.

---

## 5) Run the full test suite

```bash
pytest -q
```

Tests include:

* Prompt builder invariants
* Grounding contract checks (span offsets + substring equality)
* Offline golden mock verification
* Batch pipeline behavior

All tests should pass before proceeding to real providers.

---

## Optional: Enable caching (Phase 4 feature)

Caching stores provider outputs keyed by provider + model + prompt hash.
It is mainly useful for real providers, but works with Mock as well.

```bash
python -m mvir.cli.formalize_dir examples/problems \
  --provider mock \
  --mock-path examples/mock_llm/mock_responses.json \
  --out-dir out/mvir \
  --report out/report.json \
  --cache-dir .mvir_cache
```

---

## Invariants and Design Notes

* Preprocess is **lossless**:

  * no normalization
  * no semantic inference
  * exact preservation of whitespace and newlines
* MVIR grounding is strict:

  * `s0` must cover the full source text
  * every span text must equal `source.text[start:end]`
  * all trace references must point to existing spans
* Failures are **explicit and classified**, never silent

These invariants prevent LLM drift and make debugging precise and reproducible.

---