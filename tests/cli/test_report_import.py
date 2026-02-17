"""Import smoke test for report CLI module."""

from __future__ import annotations


def test_report_cli_import() -> None:
    import mvir.cli.report

    assert mvir.cli.report

