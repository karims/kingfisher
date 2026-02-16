# Operator Extensibility

This document describes the minimal workflow for adding operators in MVIR.

## Registry Location

- Registry file: `mvir/core/operators.py`
- Default instance: `DEFAULT_REGISTRY`
- Main types: `OperatorSpec`, `OperatorRegistry`

Add new operators in `DEFAULT_REGISTRY` so there is one source of truth for:
- canonical operator id
- accepted surface forms (LaTeX, Unicode, plain aliases)
- arity and argument roles
- target MVIR AST node

## Add A New Operator

1. Open `mvir/core/operators.py`.
2. Add an `OperatorSpec` entry to `DEFAULT_REGISTRY`.
3. Include canonical id, surface forms, arity/roles, and AST mapping.

Example: set intersection

```python
OperatorSpec(
    canonical_id="set_intersection",
    ast_node="Call",  # placeholder until dedicated node exists
    surface_forms=(r"\\cap", "∩", "intersection"),
    arity=None,
    argument_roles=("args",),
    emit_call_fn="intersection",
)
```

Example: integral

```python
OperatorSpec(
    canonical_id="integral",
    ast_node="Call",  # placeholder until dedicated node exists
    surface_forms=(r"\\int", "∫", "integral"),
    arity=None,
    argument_roles=("args",),
    emit_call_fn="integral",
)
```

## How Parser And Normalizer Use It

- Parsers/token mappers can resolve symbols/aliases through `DEFAULT_REGISTRY.lookup(...)`.
- AST normalization in `mvir/core/ast_normalize.py` can canonicalize node/operator names using the registry.
- Internal contract validation in `mvir/core/ast_contract.py` enforces required AST shape before Pydantic parsing.

## Add Tests

1. Add/extend registry tests in `tests/test_operators.py`:
   - LaTeX alias lookup
   - Unicode alias lookup
   - plain-word alias lookup
   - canonical lookup by AST node
2. Add/extend normalization+contract integration tests in `tests/test_ast_normalize_contract_integration.py`.
3. If extraction behavior changes, add flow coverage in `tests/test_formalize_normalization_hook.py`.
