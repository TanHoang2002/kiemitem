"""Tests for src.giaoit.models dataclasses."""

from types import SimpleNamespace

from src.giaoit.models import CaptureBundle, CapturedItem, CaptureMeta


def test_capture_meta_default_fields() -> None:
    meta = CaptureMeta(capture_id="abc", captured_at="2026-08-12T00:00:00+00:00", machine_id="m1")
    assert meta.capture_id == "abc"
    assert meta.captured_at == "2026-08-12T00:00:00+00:00"
    assert meta.machine_id == "m1"


def test_capture_bundle_defaults_stash_tabs_empty() -> None:
    bundle = CaptureBundle(kind="single", items=[], source="f2_key")
    assert bundle.stash_tabs_scanned == []


def test_captured_item_holds_item_and_image() -> None:
    fake_item = SimpleNamespace(name=" helm ")
    fake_img = object()
    captured = CapturedItem(item=fake_item, image=fake_img)
    assert captured.item is fake_item
    assert captured.image is fake_img
    assert captured.image_file is None
