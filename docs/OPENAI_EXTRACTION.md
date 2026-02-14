# OpenAI Extraction

This guide explains how to run MVIR extraction with OpenAI and how to debug failures.

## Environment Variables

Set these environment variables before running:

- `OPENAI_API_KEY` (required)
- `OPENAI_MODEL` (recommended, model name)
- `OPENAI_BASE_URL` (optional, defaults to OpenAI API base URL)

## Recommended Command (json_schema)

```bash
python -m mvir.cli.formalize examples/problems/latex_smoke_01.txt --provider openai --out out/openai_smoke.json --debug-dir out/debug
```

## Fallback Command (json_object)

```bash
python -m mvir.cli.formalize examples/problems/latex_smoke_01.txt --provider openai --openai-format json_object --openai-allow-fallback --out out/openai_smoke.json --debug-dir out/debug
```

## Debug Bundle Contents

When extraction fails and `--debug-dir` is set, inspect:

- `request.json`: exact request payload sent to OpenAI
- `response.json`: parsed JSON response (if available)
- `raw_output.txt`: raw text output from the provider
- `error.txt`: classified failure details and traceback

