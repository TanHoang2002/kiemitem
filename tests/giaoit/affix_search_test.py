"""Tests for src.giaoit.affix_search."""

import importlib

from src.giaoit import affix_search as giaoit_affix_search


def test_module_imports() -> None:
    assert hasattr(giaoit_affix_search, "AffixSearchDialog")
    assert hasattr(giaoit_affix_search, "AffixSearchRow")


def teardown_module(module) -> None:  # noqa: ANN001
    importlib.reload(giaoit_affix_search)
