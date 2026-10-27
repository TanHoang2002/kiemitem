"""Tests for src.giaoit.api."""

from src.giaoit.api import LocalApiHandler, start_local_api


def test_symbols_importable() -> None:
    assert LocalApiHandler is not None
    assert callable(start_local_api)
