"""Tests for deterministic MVIR trace graph export."""

from __future__ import annotations

import json
from pathlib import Path

from mvir.analysis.trace_graph import build_trace_graph
from mvir.core.models import load_mvir


def test_build_trace_graph_latex_smoke_01_has_goal_entity_and_edge() -> None:
    mvir = load_mvir(str(Path("out/mvir/latex_smoke_01.json")))

    graph = build_trace_graph(mvir)

    node_ids = {node["id"] for node in graph["nodes"]}
    assert "goal" in node_ids
    assert "entity:x" in node_ids

    assert any(
        edge["src"] == "entity:x" and edge["dst"] == "goal" and edge["type"] == "mentions"
        for edge in graph["edges"]
    )


def test_build_trace_graph_is_deterministic() -> None:
    mvir = load_mvir(str(Path("out/mvir/latex_smoke_01.json")))

    graph_a = build_trace_graph(mvir)
    graph_b = build_trace_graph(mvir)

    assert json.dumps(graph_a, sort_keys=True) == json.dumps(graph_b, sort_keys=True)

