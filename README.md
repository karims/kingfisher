# Kingfisher

Autoformalization Layer for Symbolic Math AI

Kingfisher converts natural language math problems into a structured
Mathematical Intermediate Representation (MVIR) that can be consumed by:

- symbolic solvers
- theorem provers
- hybrid AI reasoning systems

Think of it as a compiler front-end for mathematical reasoning.

## Goals

- English → structured math IR
- debuggable + validated output
- concept-aware representation
- foundation for symbolic AI

## Why Kingfisher?

Modern LLMs are strong at language but weak at maintaining precise symbolic state.
Formal systems are precise but hard to connect to natural language.

Kingfisher exists to bridge this gap.

It provides:
- a clean boundary between language understanding and symbolic reasoning
- a debuggable representation (with traceability)
- a common interface for multiple math solvers and AI systems

Think of Kingfisher as a **compiler front-end for mathematical reasoning**.

## What is MVIR?

MVIR stands for **Mathematical Virtual Intermediate Representation**.

MVIR is a compiler-style intermediate representation for mathematics.  
It captures the *mathematical state* of a problem in a structured, solver-agnostic form.

An MVIR instance includes:
- mathematical entities (variables, functions, sets)
- assumptions and constraints
- the goal (prove, find, compute, etc.)
- expression trees (AST)
- high-level mathematical concepts (e.g. inequalities, induction, AM–GM)
- trace information linking every object back to the source text

MVIR is not a proof.  
It is the **front-end representation** that downstream symbolic systems, theorem provers,
or hybrid AI models can operate on.

## Non-goals (early versions)

Kingfisher does NOT aim to:
- generate full formal proofs
- replace theorem provers
- solve math problems end-to-end

Its job is to **formalize**, not to **prove**.

## Running golden regression

Run the golden regression checker against baseline MVIR JSON files in `out/mvir`:

```bash
python -m mvir.cli.golden --provider openai --openai-allow-fallback
```

Useful flags:
- `--input-dir out/mvir` to change baseline location
- `--provider mock --mock-path examples/mock_llm/mock_responses.json` for offline/mock runs
- `--openai-format json_object` or `--openai-format json_schema`

## Phase 10 Artifacts

Formalize with optional solver bundle export:

```bash
python -m mvir.cli.formalize examples/problems/latex_smoke_01.txt --provider openai --out out/mvir/latex_smoke_01.json --bundle-out out/mvir/latex_smoke_01.bundle.json
```

Build a solver bundle from an existing MVIR JSON:

```bash
python -m mvir.cli.bundle out/mvir/latex_smoke_01.json --out out/mvir/latex_smoke_01.bundle.json
```

