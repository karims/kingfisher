# Extraction Stability

This document explains how to run golden extraction checks and why the extraction
pipeline includes normalization and repair steps.

## Run Golden Regression

```bash
python scripts/run_golden.py
```

## Run Golden Regression With OpenAI

Windows PowerShell:

```powershell
set OPENAI_API_KEY=...
python scripts/run_golden.py
```

macOS/Linux:

```bash
export OPENAI_API_KEY=...
python scripts/run_golden.py
```

## Output Location

Golden and extraction artifacts should be written under `out/`.
The repository already ignores `out/` in `.gitignore`.

## Why Normalization + Repair Exists

LLM outputs can drift over time across model versions and providers. Even when the
JSON is close to valid, small AST shape differences can break strict validation.

To keep extraction stable, the pipeline applies:

1. Deterministic normalization of near-valid JSON/AST shapes.
2. Deterministic AST repair from grounded span text where possible.
3. Strict MVIR schema + grounding validation.

If strict validation still fails, the pipeline can run a model repair pass with
tight constraints.

## Fallback Modes

The OpenAI extraction path uses progressive fallback:

1. `json_schema` strict mode (preferred when accepted by model/API).
2. `json_object` mode with JSON-only instruction (if enabled and strict schema is unsupported).
3. Repair loop: ask the model to correct invalid JSON/MVIR, then re-run deterministic normalization/repair and validation.

This layered strategy keeps behavior robust under long-term model churn while
preserving deterministic validation rules.

