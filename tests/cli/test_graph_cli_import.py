"""Import smoke test for graph CLI module."""

from __future__ import annotations


def test_graph_cli_import() -> None:
    import mvir.cli.graph

    assert mvir.cli.graph

