"""Deterministic LaTeX surface tokenizer and best-effort parser."""

from __future__ import annotations

from dataclasses import dataclass


_OPS = {"+", "-", "*", "/", "^", "_", "=", ","}
_OPEN_TO_CLOSE = {"(": ")", "{": "}", "[": "]"}
_CLOSE = {")", "}", "]"}
_BIN_PRECEDENCE = {"+": 10, "-": 10, "*": 20, "/": 20, "=": 5}


@dataclass(frozen=True)
class SurfaceParseResult:
    status: str
    raw_latex: str
    tokens: list[str]
    sexpr: str | None
    warnings: list[str]


def tokenize_math(latex: str) -> list[str]:
    """Tokenize a LaTeX math snippet into a deterministic token sequence."""

    out: list[str] = []
    i = 0
    n = len(latex)
    while i < n:
        ch = latex[i]
        if ch.isspace():
            i += 1
            continue
        if ch == "\\":
            j = i + 1
            while j < n and latex[j].isalpha():
                j += 1
            if j > i + 1:
                out.append(latex[i:j])
                i = j
            elif j < n:
                out.append(latex[i : j + 1])
                i = j + 1
            else:
                out.append("\\")
                i += 1
            continue
        if ch.isdigit():
            j = i + 1
            while j < n and latex[j].isdigit():
                j += 1
            if j < n and latex[j] == ".":
                j += 1
                while j < n and latex[j].isdigit():
                    j += 1
            out.append(latex[i:j])
            i = j
            continue
        if ch.isalpha():
            j = i + 1
            while j < n and latex[j].isalnum():
                j += 1
            out.append(latex[i:j])
            i = j
            continue
        if ch in _OPS or ch in _OPEN_TO_CLOSE or ch in _CLOSE:
            out.append(ch)
            i += 1
            continue
        out.append(ch)
        i += 1
    return out


class _Parser:
    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.i = 0
        self.warnings: list[str] = []

    def _peek(self) -> str | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def _pop(self) -> str | None:
        tok = self._peek()
        if tok is not None:
            self.i += 1
        return tok

    def _expect(self, token: str) -> bool:
        if self._peek() == token:
            self.i += 1
            return True
        self.warnings.append(f"expected '{token}' near token index {self.i}")
        return False

    def parse(self):
        expr = self._parse_expr(0)
        if expr is None:
            return None
        if self._peek() is not None:
            self.warnings.append(f"unparsed trailing tokens from index {self.i}")
        return expr

    def _parse_expr(self, min_prec: int):
        left = self._parse_prefix()
        if left is None:
            return None

        while True:
            op = self._peek()
            if op is None:
                break
            if op in _CLOSE:
                break
            if self._is_implicit_mul_boundary(op):
                op = "*"
            if op not in _BIN_PRECEDENCE:
                break
            prec = _BIN_PRECEDENCE[op]
            if prec < min_prec:
                break
            if op != "*":
                self._pop()
            rhs = self._parse_expr(prec + 1)
            if rhs is None:
                self.warnings.append(f"missing rhs for operator '{op}'")
                break
            left = self._make_bin(op, left, rhs)

        return left

    def _is_implicit_mul_boundary(self, next_token: str) -> bool:
        if next_token in _OPS or next_token in _CLOSE:
            return False
        return True

    def _parse_prefix(self):
        tok = self._peek()
        if tok is None:
            return None

        if tok in {"+", "-"}:
            self._pop()
            arg = self._parse_prefix()
            if arg is None:
                self.warnings.append("unary operator without operand")
                return ("Atom", tok)
            if tok == "-":
                return ("Neg", arg)
            return arg

        node = self._parse_primary()
        if node is None:
            return None

        while self._peek() in {"^", "_"}:
            op = self._pop()
            rhs = self._parse_primary()
            if rhs is None:
                self.warnings.append(f"missing rhs for '{op}'")
                break
            node = ("Pow", node, rhs) if op == "^" else ("Sub", node, rhs)

        return node

    def _parse_primary(self):
        tok = self._peek()
        if tok is None:
            return None

        if tok in _OPEN_TO_CLOSE:
            open_tok = self._pop()
            close_tok = _OPEN_TO_CLOSE[open_tok]
            inner = self._parse_expr(0)
            self._expect(close_tok)
            return inner if inner is not None else ("Atom", open_tok + close_tok)

        if tok.startswith("\\"):
            return self._parse_macro()

        self._pop()
        if tok in _CLOSE:
            self.warnings.append(f"unexpected closing token '{tok}'")
        return ("Atom", tok)

    def _parse_group_or_primary(self):
        tok = self._peek()
        if tok == "{":
            self._pop()
            node = self._parse_expr(0)
            self._expect("}")
            return node
        return self._parse_primary()

    def _parse_macro(self):
        macro = self._pop()
        assert macro is not None
        if macro == "\\frac":
            num = self._parse_group_or_primary()
            den = self._parse_group_or_primary()
            if num is None or den is None:
                self.warnings.append(r"\frac missing argument")
                return ("Atom", macro)
            return ("Div", num, den)
        if macro == "\\sqrt":
            arg = self._parse_group_or_primary()
            if arg is None:
                self.warnings.append(r"\sqrt missing argument")
                return ("Atom", macro)
            return ("Call", "sqrt", arg)
        if macro == "\\binom":
            a = self._parse_group_or_primary()
            b = self._parse_group_or_primary()
            if a is None or b is None:
                self.warnings.append(r"\binom missing argument")
                return ("Atom", macro)
            return ("Call", "binom", a, b)
        if macro in {"\\sum", "\\prod"}:
            return self._parse_aggregate(macro)

        self.warnings.append(f"unsupported macro {macro}")
        return ("Atom", macro)

    def _parse_aggregate(self, macro: str):
        lower = None
        upper = None

        if self._peek() == "_":
            self._pop()
            lower = self._parse_group_or_primary()
        if self._peek() == "^":
            self._pop()
            upper = self._parse_group_or_primary()
        if lower is None and self._peek() == "_":
            self._pop()
            lower = self._parse_group_or_primary()

        body = self._parse_expr(30)
        if body is None:
            body = ("Atom", "?")
            self.warnings.append(f"{macro} missing body")

        var, lower_from = self._parse_lower_bound(lower)
        upper_to = upper if upper is not None else ("Atom", "?")
        if lower is None or upper is None:
            self.warnings.append(f"{macro} incomplete bounds")

        head = "Sum" if macro == "\\sum" else "Prod"
        return (head, var, lower_from, upper_to, body)

    def _parse_lower_bound(self, lower):
        if lower is None:
            return ("Atom", "?"), ("Atom", "?")
        if isinstance(lower, tuple) and len(lower) == 3 and lower[0] == "Eq":
            lhs = lower[1]
            rhs = lower[2]
            return lhs, rhs
        self.warnings.append("lower bound not in var=from form")
        return ("Atom", "?"), lower

    def _make_bin(self, op: str, lhs, rhs):
        if op == "+":
            return ("Add", lhs, rhs)
        if op == "-":
            return ("Sub", lhs, rhs)
        if op == "*":
            return ("Mul", lhs, rhs)
        if op == "/":
            return ("Div", lhs, rhs)
        if op == "=":
            return ("Eq", lhs, rhs)
        return ("Call", op, lhs, rhs)


def _sexpr(node) -> str:
    if node is None:
        return "?"
    if isinstance(node, tuple):
        tag = node[0]
        if tag == "Atom":
            return str(node[1])
        if tag == "Call":
            return f"(Call {node[1]} " + " ".join(_sexpr(part) for part in node[2:]) + ")"
        return f"({tag} " + " ".join(_sexpr(part) for part in node[1:]) + ")"
    return str(node)


def parse_surface(latex: str) -> SurfaceParseResult:
    """Parse LaTeX into a best-effort surface representation."""

    raw_tokens = tokenize_math(latex)
    tokens = sorted(raw_tokens)
    parser = _Parser(raw_tokens)
    try:
        ast = parser.parse()
    except Exception as exc:  # noqa: BLE001 - safe fallback path
        return SurfaceParseResult(
            status="raw",
            raw_latex=latex,
            tokens=tokens,
            sexpr=None,
            warnings=[f"surface parse failed: {exc}"],
        )

    if ast is None:
        return SurfaceParseResult(
            status="raw",
            raw_latex=latex,
            tokens=tokens,
            sexpr=None,
            warnings=parser.warnings or ["could not parse expression"],
        )

    sexpr = _sexpr(ast)
    status = "ok" if not parser.warnings else "partial"
    return SurfaceParseResult(
        status=status,
        raw_latex=latex,
        tokens=tokens,
        sexpr=sexpr,
        warnings=parser.warnings,
    )

