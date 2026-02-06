# Validation Rules — v0.1

Validation turns MVIR into a compiler-like artifact:
it must be schema-valid, type-consistent, and constraint-aware.

Validator outputs:
- `errors` (fail compilation)
- `warnings` (non-fatal issues; e.g. assumption debt)

---

## A) Schema validation (errors)

1. MVIR must conform to JSON schema for version `0.1`.
2. Required top-level fields: `meta, source, entities, assumptions, goal, trace`.

---

## B) Entity & reference checks (errors)

1. Every `Symbol.id` in AST must reference an entity in `entities`.
2. Entity IDs must be unique.
3. Goal `expr` must be present for `goal.kind=prove`.

---

## C) Type checks (errors in v0.1 where possible)

1. Numeric ops require numeric types (Real/Integer/Natural/Rational).
2. Comparisons require comparable numeric types.
3. If type is unknown, emit warning `TYPE_UNCERTAIN`.

---

## D) Domain/operation safety (warnings or errors)

### Division safety
- If expression contains `Div(num, den)` and `den` can be zero:
  - If assumptions imply `den != 0` (or `den > 0` / `den < 0`), OK.
  - Otherwise emit warning `ASSUMPTION_DEBT` with suggested constraint `den != 0`.

### sqrt safety
- If expression contains `Call(fn="sqrt", args=[x])`:
  - Requires `x >= 0`.
  - Otherwise emit warning `ASSUMPTION_DEBT` suggesting `x >= 0`.

### log safety
- If expression contains `Call(fn="log", args=[x])`:
  - Requires `x > 0`.
  - Otherwise emit warning `ASSUMPTION_DEBT` suggesting `x > 0`.

---

## E) Ambiguity handling (warnings)

- If extractor indicates multiple parses or low confidence:
  - emit `AMBIGUITY` warning with alternatives if available.

---

## F) Trace checks (warnings)

- Each entity/assumption/goal/concept SHOULD have trace spans.
- Missing trace emits `MISSING_TRACE` warning.
