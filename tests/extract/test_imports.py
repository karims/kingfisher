"""Import tests for Phase 3 extraction scaffolding."""

from __future__ import annotations


def test_extract_imports() -> None:
    import mvir.extract.context
    import mvir.extract.contract
    import mvir.extract.formalize
    import mvir.extract.prompts
    import mvir.extract.provider_base
    import mvir.extract.providers
    import mvir.extract.providers.mock
    import mvir.cli.formalize

    assert mvir.extract.context
    assert mvir.extract.contract
    assert mvir.extract.formalize
    assert mvir.extract.prompts
    assert mvir.extract.provider_base
    assert mvir.extract.providers
    assert mvir.extract.providers.mock
    assert mvir.cli.formalize
