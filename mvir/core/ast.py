"""AST node definitions for MVIR."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class Symbol(BaseModel):
    """Identifier symbol."""

    node: Literal["Symbol"]
    id: str = Field(min_length=1)


class Number(BaseModel):
    """Numeric literal."""

    node: Literal["Number"]
    value: int | float


class Bool(BaseModel):
    """Boolean literal."""

    node: Literal["Bool", "True", "False"]
    value: bool


class Add(BaseModel):
    """Addition over one or more arguments."""

    node: Literal["Add"]
    args: list["Expr"] = Field(min_length=1)


class Mul(BaseModel):
    """Multiplication over one or more arguments."""

    node: Literal["Mul"]
    args: list["Expr"] = Field(min_length=1)


class Div(BaseModel):
    """Division of numerator by denominator."""

    node: Literal["Div"]
    num: "Expr"
    den: "Expr"


class Pow(BaseModel):
    """Exponentiation."""

    node: Literal["Pow"]
    base: "Expr"
    exp: "Expr"


class Neg(BaseModel):
    """Negation."""

    node: Literal["Neg"]
    arg: "Expr"


class Eq(BaseModel):
    """Equality comparison."""

    node: Literal["Eq"]
    lhs: "Expr"
    rhs: "Expr"


class Neq(BaseModel):
    """Inequality comparison."""

    node: Literal["Neq"]
    lhs: "Expr"
    rhs: "Expr"


class Lt(BaseModel):
    """Less-than comparison."""

    node: Literal["Lt"]
    lhs: "Expr"
    rhs: "Expr"


class Le(BaseModel):
    """Less-than-or-equal comparison."""

    node: Literal["Le"]
    lhs: "Expr"
    rhs: "Expr"


class Gt(BaseModel):
    """Greater-than comparison."""

    node: Literal["Gt"]
    lhs: "Expr"
    rhs: "Expr"


class Ge(BaseModel):
    """Greater-than-or-equal comparison."""

    node: Literal["Ge"]
    lhs: "Expr"
    rhs: "Expr"


class Divides(BaseModel):
    """Divisibility relation."""

    node: Literal["Divides"]
    lhs: "Expr"
    rhs: "Expr"


class Sum(BaseModel):
    """Summation expression."""

    model_config = ConfigDict(populate_by_name=True)

    node: Literal["Sum"]
    var: str = Field(min_length=1)
    from_: "Expr" = Field(alias="from")
    to: "Expr"
    body: "Expr"


class Call(BaseModel):
    """Function call."""

    node: Literal["Call"]
    fn: str = Field(min_length=1)
    args: list["Expr"]


Expr = Annotated[
    Union[
        Symbol,
        Number,
        Bool,
        Add,
        Mul,
        Div,
        Pow,
        Neg,
        Eq,
        Neq,
        Lt,
        Le,
        Gt,
        Ge,
        Divides,
        Sum,
        Call,
    ],
    Field(discriminator="node"),
]


def parse_expr(data: dict) -> Expr:
    """Parse and validate a dict into an Expr."""

    return TypeAdapter(Expr).validate_python(data)


def expr_to_dict(expr: Expr) -> dict:
    """Serialize an Expr into a dict."""

    return expr.model_dump(by_alias=False, exclude_none=True)
