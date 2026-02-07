"""Import tests for Phase 4 scaffolding modules."""

from __future__ import annotations


def test_phase4_imports() -> None:
    import mvir.cli.formalize_dir
    import mvir.extract.cache
    import mvir.extract.providers.ollama_provider
    import mvir.extract.providers.openai_provider
    import mvir.extract.report

    assert mvir.cli.formalize_dir
    assert mvir.extract.cache
    assert mvir.extract.providers.openai_provider
    assert mvir.extract.providers.ollama_provider
    assert mvir.extract.report

