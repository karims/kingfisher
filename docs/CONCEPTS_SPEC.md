# Concepts — Spec v0.1

Concepts are structured tags that capture the *mathematical territory* of a problem:
domain, patterns, candidate tools, and representation hints.

Concepts must be:
- **structured** (stable IDs)
- **auditable** (trace spans)
- **actionable** (roles usable by later solvers)

## Concept roles (v0.1)

- `domain`: broad area (e.g. algebra, inequality, number theory, geometry)
- `pattern`: recognizable problem shape (e.g. reciprocal sum, symmetry)
- `candidate_tool`: lemmas/techniques (e.g. AM-GM, Cauchy-Schwarz)
- `definition`: key definitions involved (prime, gcd, continuous)
- `representation_hint`: suggestions for representation changes (substitution, normalization)

## Concept registry

A concept registry maps stable IDs to metadata.

Recommended format: `concepts/registry.json` (or yaml later).

Minimal fields:
- `id`
- `name`
- `roles` (allowed roles)
- `prerequisites` (optional, e.g. requires nonnegativity)
- `aliases` (optional)
- `notes` (optional)

## Emission rules (v0.1)

- The extractor MAY emit concept tags with `confidence`.
- The validator SHOULD verify that `concept.id` exists in the registry.
- Concepts must include `role`.
- Concepts should include `trace`.

## Initial concept set (starter list)

Domains:
- `domain_algebra`
- `domain_inequality`
- `domain_number_theory`
- `domain_geometry`

Patterns:
- `pattern_reciprocal_sum`
- `pattern_symmetry`
- `pattern_bounding`
- `pattern_monotonicity`

Candidate tools:
- `tool_amgm`
- `tool_cauchy_schwarz`
- `tool_triangle_inequality`
- `tool_induction`

Representation hints:
- `hint_substitution`
- `hint_normalize`
- `hint_wlog_ordering`
