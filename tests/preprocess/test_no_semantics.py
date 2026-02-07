"""Preprocess outputs should not include semantic fields."""

from __future__ import annotations

from mvir.preprocess.context import build_preprocess_output


def test_preprocess_no_semantic_keys() -> None:
    output = build_preprocess_output("Show that for any x, x + 1/x >= 2.")
    payload = output.to_dict()

    forbidden = {"entities", "assumptions", "goal", "concepts", "warnings"}
    assert forbidden.isdisjoint(payload.keys())

    allowed_cues = {
        "VERB_PROVE",
        "VERB_FIND",
        "VERB_COMPUTE",
        "PHRASE_ASSUME",
        "PHRASE_LET",
        "PHRASE_QUANTIFIER",
        "PHRASE_CONSTRAINT",
    }
    for cue in payload["cue_candidates"]:
        assert cue["category"] in allowed_cues
