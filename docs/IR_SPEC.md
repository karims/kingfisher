# Kingfisher MVIR (Math IR) — Spec v0.1

Kingfisher converts natural-language math problems into a structured, debuggable
Mathematical Intermediate Representation (MVIR). MVIR is a *state representation*,
not a proof.

## Design principles

- **JSON is the source of truth** (schema-validated).
- **Markdown is a derived view** generated from JSON.
- **Traceability**: every extracted item should be attributable to source text spans.
- **Symbol-native**: math objects + constraints are first-class.
- **Non-goals (v0.1)**: generating full proofs, theorem proving, multi-branch search.

---

## MVIR top-level structure

MVIR is a JSON object with the following top-level fields:

- `meta`
- `source`
- `entities`
- `assumptions`
- `goal`
- `concepts`
- `warnings`
- `trace`

### 1) `meta`

Required.

- `version`: string, e.g. `"0.1"`
- `id`: string (stable identifier, e.g. hash)
- `created_at`: ISO timestamp (optional in v0.1)
- `generator`: string (e.g. `"kingfisher-cli"`)

### 2) `source`

Required.

- `text`: original problem text
- `normalized_text`: optional
- `spans`: optional list of detected math spans (for debugging)

### 3) `entities`

Required. List of math objects in scope.

Entity fields:
- `id`: string (e.g. `"x"`, `"n"`, `"f"`, `"A"`)
- `kind`: enum: `variable | constant | function | set | sequence | point | vector | object`
- `type`: type descriptor (see below)
- `properties`: optional list of property tags (e.g. `["continuous"]`)
- `trace`: span reference(s)

#### Type descriptor (v0.1 minimal)
- atomic: `Real | Integer | Natural | Rational | Complex | Bool`
- structured:
  - `Interval(Real, a, b)` (represented as object)
  - `Function(domain_type, codomain_type)`
  - `Sequence(index_type, value_type)`
  - `Set(of_type)`
  - `Point2D | Point3D` (optional for v0.1)

### 4) `assumptions`

Required. List of constraints/assumptions.

Assumption fields:
- `id`: optional stable id
- `expr`: boolean expression AST (see AST section)
- `kind`: enum: `given | derived | wlog`
- `trace`: span reference(s)

### 5) `goal`

Required. The goal specification.

Goal fields:
- `kind`: enum: `prove | find | compute | maximize | minimize | exists | counterexample`
- `expr`: expression AST (for `prove`, typically a boolean comparison)
- `target`: optional (for `find`, `compute`, etc.)
- `trace`: span reference(s)

### 6) `concepts`

Optional but recommended. Structured concept tags.

Concept fields:
- `id`: stable key from concept registry (e.g. `tool_amgm`)
- `name`: human name (optional if registry is available)
- `role`: enum: `domain | pattern | candidate_tool | definition | representation_hint`
- `trigger`: short string (why it was suggested)
- `confidence`: optional float [0,1]
- `trace`: span reference(s)

### 7) `warnings`

Optional list of issues that are not fatal.

Warning fields:
- `code`: e.g. `ASSUMPTION_DEBT`, `AMBIGUITY`, `TYPE_UNCERTAIN`
- `message`: human readable
- `details`: optional structured payload
- `trace`: span reference(s)

### 8) `trace`

Required. List of source spans and extraction notes.

Span representation:
- `span_id`: string
- `start`: int (char offset in `source.text`)
- `end`: int
- `text`: snippet (optional but helpful)

---

## Expression AST (v0.1)

All mathematical expressions are represented as JSON AST nodes.

### Node types

- `Symbol`: `{ "node": "Symbol", "id": "x" }`
- `Number`: `{ "node": "Number", "value": 2 }`
- `Add`: `{ "node": "Add", "args": [ ... ] }`
- `Mul`: `{ "node": "Mul", "args": [ ... ] }`
- `Div`: `{ "node": "Div", "num": <expr>, "den": <expr> }`
- `Pow`: `{ "node": "Pow", "base": <expr>, "exp": <expr> }`
- `Neg`: `{ "node": "Neg", "arg": <expr> }`

### Comparisons (boolean)
- `Eq`, `Neq`, `Lt`, `Le`, `Gt`, `Ge`:
  - `{ "node": "Ge", "lhs": <expr>, "rhs": <expr> }`

### Functions (minimal)
- `Call`: `{ "node": "Call", "fn": "sqrt", "args": [<expr>] }`
  - Supported `fn` list in v0.1: `sqrt`, `log`, `abs` (extend later)

---

## Examples (v0.1)

### Example: x + 1/x >= 2

Entities:
- `x : Real`

Assumptions:
- `x > 0`

Goal:
- `prove( x + 1/x >= 2 )`

Concepts (optional):
- `pattern_reciprocal_sum`
- `tool_amgm`

---

## Versioning

- MVIR spec uses semantic-ish versions: `0.1`, `0.2`, ...
- Breaking schema changes require version bump.
