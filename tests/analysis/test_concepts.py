"""Tests for deterministic MVIR concept extraction."""

from __future__ import annotations

from pathlib import Path

from mvir.analysis.concepts import augment_mvir_with_concepts, extract_concepts
from mvir.core.models import MVIR, load_mvir


def _synthetic_mvir() -> MVIR:
    payload = {
        "meta": {"version": "0.1", "id": "concepts_case"},
        "source": {"text": "synthetic"},
        "entities": [],
        "assumptions": [
            {
                "kind": "given",
                "trace": ["s1"],
                "expr": {
                    "node": "Gt",
                    "lhs": {"node": "Symbol", "id": "x"},
                    "rhs": {"node": "Number", "value": 0},
                },
            },
            {
                "kind": "given",
                "trace": ["s2"],
                "expr": {
                    "node": "Eq",
                    "lhs": {
                        "node": "Sum",
                        "var": "k",
                        "from": {"node": "Number", "value": 1},
                        "to": {"node": "Symbol", "id": "n"},
                        "body": {"node": "Symbol", "id": "k"},
                    },
                    "rhs": {
                        "node": "Div",
                        "num": {
                            "node": "Mul",
                            "args": [
                                {"node": "Symbol", "id": "n"},
                                {
                                    "node": "Add",
                                    "args": [
                                        {"node": "Symbol", "id": "n"},
                                        {"node": "Number", "value": 1},
                                    ],
                                },
                            ],
                        },
                        "den": {"node": "Number", "value": 2},
                    },
                },
            },
        ],
        "goal": {
            "kind": "prove",
            "trace": ["s3"],
            "expr": {
                "node": "Ge",
                "lhs": {
                    "node": "Pow",
                    "base": {"node": "Symbol", "id": "x"},
                    "exp": {"node": "Number", "value": 2},
                },
                "rhs": {"node": "Number", "value": 0.0},
            },
        },
        "concepts": [{"id": "llm_hint", "role": "definition"}],
        "warnings": [],
        "trace": [
            {"span_id": "s0", "start": 0, "end": 9, "text": "synthetic"},
            {"span_id": "s1", "start": 0, "end": 3, "text": "x > 0"},
            {
                "span_id": "s2",
                "start": 4,
                "end": 8,
                "text": "sum identity",
            },
            {"span_id": "s3", "start": 0, "end": 9, "text": "x^2 >= 0"},
        ],
    }
    return MVIR.model_validate(payload)


def test_extract_concepts_is_deterministic_and_stable() -> None:
    mvir = _synthetic_mvir()

    concepts_a = extract_concepts(mvir)
    concepts_b = extract_concepts(mvir)

    assert [c.id for c in concepts_a] == [
        "nonnegativity_of_square",
        "positivity:x",
        "sum_of_first_n_integers",
    ]
    assert [c.model_dump() for c in concepts_a] == [c.model_dump() for c in concepts_b]
    assert concepts_a[0].trace == ["s3"]

    augmented = augment_mvir_with_concepts(mvir)
    assert [c.id for c in augmented.concepts] == [c.id for c in concepts_a]


def test_latex_smoke_01_fixture_concepts() -> None:
    fixture_path = Path("out/mvir/latex_smoke_01.json")
    mvir = load_mvir(str(fixture_path))

    augmented_a = augment_mvir_with_concepts(mvir)
    augmented_b = augment_mvir_with_concepts(mvir)

    assert [c.id for c in augmented_a.concepts] == ["nonnegativity_of_square"]
    assert augmented_a.concepts[0].role.value == "pattern"
    assert augmented_a.concepts[0].trace == ["s3"]
    assert [c.model_dump() for c in augmented_a.concepts] == [
        c.model_dump() for c in augmented_b.concepts
    ]

