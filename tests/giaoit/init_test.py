"""Smoke test: importing the public surface of src.giaoit does not error."""

from src import giaoit


def test_public_symbols_importable() -> None:
    assert giaoit.CaptureBundle is not None
    assert giaoit.CaptureMeta is not None
    assert giaoit.CapturedItem is not None
    assert callable(giaoit.is_capture_enabled)
    assert callable(giaoit.machine_id)
