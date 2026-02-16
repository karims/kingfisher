# Solver Trace (MVIR v0.1)

`solver_trace` is an optional top-level block in MVIR for structured solver-action logging.

This is a representation layer only. It does not perform solving by itself.

## Purpose

- Keep solver-side actions in a consistent machine-readable format.
- Support future UI/debug timelines and RL-style trajectory analysis.
- Preserve backward compatibility with existing MVIR files.

## Shape

Top-level MVIR field:
- `solver_trace`: `object | null` (optional)

`solver_trace` fields:
- `schema_version`: constant `"0.1"`
- `events`: list of `SolverEvent` (default `[]`)
- `summary`: optional string
- `metrics`: optional map (`str -> float|int|str|bool`)
- `artifacts`: optional map (`str -> str`) for ids/paths only

`SolverEvent` fields:
- `event_id`: string
- `ts`: optional ISO8601 string
- `kind`: one of
  - `plan`, `claim`, `transform`, `tool_call`, `tool_result`, `branch`, `backtrack`, `final`, `note`, `error`
- `message`: string
- `data`: optional object payload
- `trace`: optional list of trace span ids
- `refs`: optional list of ids (entities/assumptions/etc.)

## Compatibility

- Existing MVIR JSON without `solver_trace` remains valid.
- OpenAI subset schema includes `solver_trace` as an optional top-level property.
