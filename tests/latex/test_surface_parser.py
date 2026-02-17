from __future__ import annotations

from mvir.latex.surface import parse_surface, tokenize_math


def test_frac_surface_parse() -> None:
    result = parse_surface(r"\frac{n(n+1)}{2}")

    assert result.status in {"ok", "partial"}
    assert result.tokens
    assert result.sexpr is not None
    assert "(Div " in result.sexpr
    assert "n" in result.sexpr


def test_sum_surface_parse() -> None:
    result = parse_surface(r"\sum_{k=1}^n k")

    assert result.status in {"ok", "partial"}
    assert result.tokens
    assert result.sexpr is not None
    assert result.sexpr.startswith("(Sum ")


def test_geometry_unsupported_fallback_is_safe() -> None:
    result = parse_surface(r"\angle ABC = 90^\circ")

    assert result.status in {"partial", "raw"}
    assert result.raw_latex == r"\angle ABC = 90^\circ"
    assert result.tokens
    assert isinstance(result.warnings, list)


def test_tokenizer_is_deterministic() -> None:
    latex = r"\frac{n(n+1)}{2}"
    a = tokenize_math(latex)
    b = tokenize_math(latex)

    assert a == b
    assert a

