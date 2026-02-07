# Design Decisions — Kingfisher

This document records **intentional architectural and representation decisions**
made in Kingfisher.  
Its purpose is to prevent accidental redesigns, regressions, and
schema drift as the project evolves.

When in doubt: **this document overrides convenience fixes.**

---

## 1. MVIR is a Compiler-Style IR

**Decision**
- Kingfisher produces a *Mathematical Virtual Intermediate Representation (MVIR)*.
- MVIR is analogous to a compiler IR (e.g., LLVM IR), not a solver output.

**Rationale**
- Keeps language understanding separate from symbolic reasoning.
- Enables multiple backends (SymPy, Lean, custom solvers).
- Makes debugging and benchmarking possible.

**Implication**
- MVIR must be stable, explicit, and inspectable.
- MVIR is not optimized for human writing, but for machine correctness.

---

## 2. JSON Is the Source of Truth

**Decision**
- JSON is the authoritative representation of MVIR.
- Markdown or other views are derived outputs only.

**Rationale**
- JSON is schema-validatable and deterministic.
- Enables automated testing, CI, and tooling.

**Implication**
- No logic should depend on Markdown.
- Any change must preserve JSON schema validity.

---

## 3. AST Core vs Extension Boundary

**Decision**
- MVIR v0.1 defines a **small, frozen core AST**.
- Any construct not in the core MUST be represented using:
  - `Call(fn=..., args=...)`, or
  - an explicit extension mechanism in later versions.

**Core AST Nodes (v0.1)**
- Symbol
- Number
- Bool
- Add, Mul, Div, Pow, Neg
- Eq, Neq, Lt, Le, Gt, Ge
- Call

**Rationale**
- Prevents AST explosion.
- Keeps schema manageable.
- Allows future math constructs without breaking compatibility.

**Implication**
- New nodes like `Sum`, `Divides`, `Integral`, etc. MUST NOT be added directly to core.
- They must go through `Call` (or `Ext` in future versions).

---

## 4. Schema Changes Require Migration Scripts

**Decision**
- Any breaking change to MVIR schema or AST requires:
  1. A migration script (`scripts/migrate_*.py`)
  2. A documented transition period (even if short)

**Rationale**
- Prevents cascading fixture failures.
- Avoids Codex silently reshaping design to “fix tests”.

**Implication**
- Never “just update fixtures by hand” for breaking changes.
- Backwards compatibility may be temporarily supported in parsers.

---

## 5. Fixtures Are Golden, Not Disposable

**Decision**
- Files in `examples/expected/` are **golden fixtures**.
- They represent intended MVIR outputs and must remain meaningful.

**Rationale**
- Fixtures are the project’s executable specification.
- They double as documentation and regression tests.

**Implication**
- Fixtures should only change intentionally.
- When they change, explain *why* in commit messages.

---

## 6. Traceability Is Mandatory

**Decision**
- Every MVIR object (entity, assumption, goal, concept, warning)
  SHOULD reference source trace spans.
- Phase 0 allows coarse spans; later phases refine granularity.

**Rationale**
- Debuggability is a core feature.
- Enables error attribution and user trust.

**Implication**
- No “magic” extraction without trace.
- Missing trace is a warning at minimum.

---

## 7. Concepts Are Structured Tags, Not Explanations

**Decision**
- Concepts are lightweight, structured annotations.
- They are NOT free-form explanations or proofs.

**Rationale**
- Keeps MVIR compact.
- Enables downstream planning without over-committing semantics.

**Implication**
- Concepts must have:
  - stable IDs
  - defined roles
  - optional confidence + trigger
- Explanations belong elsewhere, not in MVIR.

---

## 8. Non-goals Are Explicitly Protected

**Decision**
- Kingfisher does NOT aim to:
  - solve math problems
  - generate full proofs
  - replace theorem provers

**Rationale**
- Prevents scope creep.
- Keeps the project focused and composable.

**Implication**
- Features that blur this boundary should be rejected or deferred.

---

## 9. Codex Is a Tool, Not an Architect

**Decision**
- Codex may generate code and tests.
- Codex must NOT redefine schema, AST, or architecture to “make things pass”.

**Rationale**
- Automated fixes often hide conceptual regressions.

**Implication**
- When Codex suggests structural changes:
  - stop
  - reassess design
  - update this document if change is intentional

---

## 10. Design Changes Must Update This File

**Decision**
- Any intentional architectural change MUST be recorded here.

**Rationale**
- Prevents implicit knowledge.
- Helps future contributors and future maintainers (including you).

**Implication**
- If a change feels “big”, it belongs here.

---

## 11. Preprocess Is Non-semantic

**Decision**
- Preprocess is NOT allowed to perform semantic extraction.
- Preprocess may only detect candidate spans/cues and compute offsets.

**Rationale**
- Keeps language understanding in the MVIR/LLM layer.
- Prevents silent duplication of parsing logic.

**Implication**
- Preprocess outputs must remain lightweight signals, not interpretation.

---

## 12. Phase 3 Extraction

**Decision**
- Phase 3 uses an LLM to extract MVIR semantics from prompt context.
- Unknown or context spans are allowed and must not be forced into goal or assumption slots.

**Rationale**
- Some spans are ambiguous or incomplete without downstream reasoning.
- Forcing a semantic label too early produces brittle MVIR.

**Implication**
- Providers must preserve ambiguity and avoid schema drift.
- MVIR schema remains unchanged across Phase 1/2/3.

---

## Closing Note

Kingfisher is infrastructure.

Infrastructure favors:
- clarity over cleverness
- stability over speed
- explicitness over inference

This document exists to protect those values.
