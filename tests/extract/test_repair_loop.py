"""Tests for one-shot MVIR validation repair loop."""

from __future__ import annotations

import json

from mvir.extract.formalize import formalize_text_to_mvir


class _QueuedOpenAIProvider:
    name = "openai"
    model = "test-model"

    def __init__(self, outputs: list[str]) -> None:
        self._outputs = list(outputs)
        self.prompts: list[str] = []

    def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> str:
        _ = temperature
        _ = max_tokens
        self.prompts.append(prompt)
        if not self._outputs:
            raise RuntimeError("No queued provider output")
        return self._outputs.pop(0)


def _invalid_first_payload() -> dict:
    return {
        "meta": {"version": "0.1", "id": "repair_case", "generator": "openai"},
        "source": {"text": "x"},
        "entities": [
            {
                "id": "x",
                "kind": "expression",
                "properties": [],
                "trace": ["s1"],
            }
        ],
        "assumptions": [],
        "goal": {
            "kind": "prove",
            "expr": {"node": "Bool", "value": True},
            "trace": ["s0"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 1, "text": "x"},
            {"span_id": "s1", "start": 0, "end": 1, "text": "x"},
        ],
    }


def _fixed_payload() -> dict:
    return {
        "meta": {"version": "0.1", "id": "repair_case", "generator": "openai"},
        "source": {"text": "x"},
        "entities": [
            {
                "id": "x",
                "kind": "variable",
                "type": "real",
                "properties": [],
                "trace": ["s1"],
            }
        ],
        "assumptions": [],
        "goal": {
            "kind": "prove",
            "expr": {"node": "Bool", "value": True},
            "trace": ["s0"],
        },
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 1, "text": "x"},
            {"span_id": "s1", "start": 0, "end": 1, "text": "x"},
        ],
    }


def test_validation_error_triggers_one_shot_openai_repair() -> None:
    provider = _QueuedOpenAIProvider(
        [json.dumps(_invalid_first_payload()), json.dumps(_fixed_payload())]
    )

    mvir = formalize_text_to_mvir("x", provider, problem_id="repair_case")

    assert mvir.meta.id == "repair_case"
    assert len(provider.prompts) == 2
    assert "You output JSON but it failed MVIR validation." in provider.prompts[1]
    assert "Return corrected JSON only." in provider.prompts[1]
    assert "```" not in provider.prompts[1]


def _assert_expr_required_fields(expr: dict) -> None:
    node = expr.get("node")
    assert isinstance(node, str)
    if node == "Symbol":
        assert isinstance(expr.get("id"), str) and expr["id"]
        return
    if node == "Number":
        assert "value" in expr
        return
    if node in {"Add", "Mul"}:
        args = expr.get("args")
        assert isinstance(args, list) and len(args) >= 1
        for arg in args:
            assert isinstance(arg, dict)
            _assert_expr_required_fields(arg)
        return
    if node == "Div":
        assert isinstance(expr.get("num"), dict)
        assert isinstance(expr.get("den"), dict)
        _assert_expr_required_fields(expr["num"])
        _assert_expr_required_fields(expr["den"])
        return
    if node == "Pow":
        assert isinstance(expr.get("base"), dict)
        assert isinstance(expr.get("exp"), dict)
        _assert_expr_required_fields(expr["base"])
        _assert_expr_required_fields(expr["exp"])
        return
    if node in {"Eq", "Neq", "Lt", "Le", "Gt", "Ge", "Divides"}:
        assert isinstance(expr.get("lhs"), dict)
        assert isinstance(expr.get("rhs"), dict)
        _assert_expr_required_fields(expr["lhs"])
        _assert_expr_required_fields(expr["rhs"])
        return
    if node == "Sum":
        assert isinstance(expr.get("var"), str) and expr["var"]
        assert isinstance(expr.get("from"), dict)
        assert isinstance(expr.get("to"), dict)
        assert isinstance(expr.get("body"), dict)
        _assert_expr_required_fields(expr["from"])
        _assert_expr_required_fields(expr["to"])
        _assert_expr_required_fields(expr["body"])
        return
    if node == "Call":
        assert isinstance(expr.get("fn"), str) and expr["fn"]
        args = expr.get("args")
        assert isinstance(args, list)
        for arg in args:
            assert isinstance(arg, dict)
            _assert_expr_required_fields(arg)
        return
    if node == "Bool":
        assert isinstance(expr.get("value"), bool)
        return
    raise AssertionError(f"Unexpected Expr node: {node}")


def test_repair_run_outputs_no_expr_with_missing_required_fields() -> None:
    broken_first = _invalid_first_payload()
    placeholder_second = {
        "meta": {"version": "0.1", "id": "repair_case", "generator": "openai"},
        "source": {"text": "x"},
        "entities": [
            {"id": "x", "kind": "variable", "type": "real", "properties": [], "trace": ["s1"]}
        ],
        "assumptions": [
            {
                "expr": {"node": "Gt", "lhs": {"node": "Symbol"}, "rhs": {"node": "Number"}},
                "kind": "given",
                "trace": ["s1"],
            }
        ],
        "goal": {"kind": "prove", "expr": {"node": "Add"}, "trace": ["s0"]},
        "concepts": [],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 1, "text": "x"},
            {"span_id": "s1", "start": 0, "end": 1, "text": "x"},
        ],
    }
    provider = _QueuedOpenAIProvider(
        [json.dumps(broken_first), json.dumps(placeholder_second)]
    )
    mvir = formalize_text_to_mvir("x", provider, problem_id="repair_case")
    payload = mvir.model_dump(by_alias=False, exclude_none=True)
    for assumption in payload.get("assumptions", []):
        expr = assumption.get("expr")
        assert isinstance(expr, dict)
        _assert_expr_required_fields(expr)
    goal = payload.get("goal", {})
    if isinstance(goal.get("expr"), dict):
        _assert_expr_required_fields(goal["expr"])
    if isinstance(goal.get("target"), dict):
        _assert_expr_required_fields(goal["target"])
