# Kingfisher Quickstart (OpenAI, Phase 4)

This guide shows how to run Kingfisher with the OpenAI provider after Phase 4 setup is complete.

It covers:
1. Environment configuration
2. Single-file formalization
3. Batch formalization with cache
4. Reading failure kinds in reports

---

## 1) Set OpenAI Environment Variables

Do not hardcode secrets in code. Use environment variables.

### Windows PowerShell
```powershell
$env:OPENAI_API_KEY = "YOUR_API_KEY_HERE"
$env:OPENAI_MODEL = "gpt-4.1-mini"
```

Optional custom endpoint:
```powershell
$env:OPENAI_BASE_URL = "https://api.openai.com"
```

### macOS / Linux (bash/zsh)
```bash
export OPENAI_API_KEY="YOUR_API_KEY_HERE"
export OPENAI_MODEL="gpt-4.1-mini"
```

Optional custom endpoint:
```bash
export OPENAI_BASE_URL="https://api.openai.com"
```

---

## 2) Single-File Run

```bash
python -m mvir.cli.formalize examples/problems/latex_smoke_01.txt --provider openai --out out/openai_smoke.json
```

Expected result:
- `out/openai_smoke.json` is created
- CLI prints `OK: latex_smoke_01`

---

## 3) Batch Run with Cache

```bash
python -m mvir.cli.formalize_dir examples/problems --provider openai --out-dir out/mvir_openai --report out/report_openai.json --cache-dir .mvir_cache
```

Expected result:
- One output file per successful problem in `out/mvir_openai`
- Run report written to `out/report_openai.json`
- Cache files written under `.mvir_cache`

---

## 4) Failure Kinds in Report

The report includes:
- `ok`: list of successful problem IDs
- `failed`: list of `{id, kind, message}`

`kind` values:
- `provider`: provider/network/auth/rate-limit failures
- `json_parse`: provider returned non-JSON or invalid JSON
- `schema_validation`: JSON parsed, but MVIR schema validation failed
- `grounding_contract`: MVIR failed grounding checks (trace/span integrity)

Use `message` to diagnose the exact cause for each failed ID.

