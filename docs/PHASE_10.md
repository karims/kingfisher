# Phase 10 Surface Math Layer

This phase adds a deterministic LaTeX surface parser for math snippets.

API:
- `tokenize_math(latex: str) -> list[str]`
- `parse_surface(latex: str) -> SurfaceParseResult`

`SurfaceParseResult` fields:
- `status`: `ok | partial | raw`
- `raw_latex`: original LaTeX text
- `tokens`: stable token list
- `sexpr`: best-effort S-expression (or `null`)
- `warnings`: non-fatal parser warnings

Examples:

```python
parse_surface(r"\frac{n(n+1)}{2}")
# status: ok/partial
# sexpr: (Div (Mul n (Add n 1)) 2)
```

```python
parse_surface(r"\sum_{k=1}^n k")
# status: ok/partial
# sexpr: (Sum k 1 n k)
```

```python
parse_surface(r"\angle ABC = 90^\circ")
# status: partial/raw
# warnings include unsupported macro notes
```

