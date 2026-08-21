"""Tests for src.giaoit.capture.capture_item_at_cursor."""

import importlib
from types import SimpleNamespace

import numpy as np

from src.game_data import ItemRarity, ItemType
from src.giaoit import capture as giaoit_capture
from src.giaoit.models import CaptureBundle, CapturedItem
from src.item import Affix, AffixType, Item


def _make_item() -> Item:
    return Item(
        item_type=ItemType.Helm,
        rarity=ItemRarity.Legendary,
        power=900,
        affixes=[Affix(name="armor", value=10.0, type=AffixType.normal)],
    )


def _reload(monkeypatch, tmp_path):
    monkeypatch.setenv("GIAOIT_CAPTURE_DIR", str(tmp_path))
    importlib.reload(giaoit_capture)
    return giaoit_capture


def test_capture_returns_bundle_with_image_and_item(monkeypatch, tmp_path) -> None:
    c = _reload(monkeypatch, tmp_path)

    fake_cropped = np.zeros((4, 4, 3), dtype=np.uint8)
    item = _make_item()

    monkeypatch.setattr(c, "pointer_position", lambda: (100, 200))
    monkeypatch.setattr(c, "monitor_to_window", lambda coord: (coord[0] + 1, coord[1] + 1))
    # Mock the stable tooltip helper that capture_item_at_cursor now delegates to.
    fake_detection = SimpleNamespace(found=True, cropped_descr=fake_cropped, crop_roi=None, failure_reason=None)
    import src.giaoit.stash_scan as stash_scan_mod

    monkeypatch.setattr(stash_scan_mod, "_capture_stable_tooltip", lambda anchor: (fake_detection, fake_cropped))
    monkeypatch.setattr(c, "read_latest_item", lambda: item)

    bundle = c.capture_item_at_cursor()

    assert bundle is not None
    assert bundle.kind == "single"
    assert bundle.source == "f2_key"
    assert len(bundle.items) == 1
    captured: CapturedItem = bundle.items[0]
    assert captured.item is item
    assert captured.image is fake_cropped


def test_capture_returns_bundle_when_tooltip_not_found(monkeypatch, tmp_path) -> None:
    """When no tooltip is detected, capture still records the item text (image=None)."""
    c = _reload(monkeypatch, tmp_path)

    monkeypatch.setattr(c, "pointer_position", lambda: (100, 200))
    monkeypatch.setattr(c, "monitor_to_window", lambda coord: coord)
    import src.giaoit.stash_scan as stash_scan_mod

    monkeypatch.setattr(stash_scan_mod, "_capture_stable_tooltip", lambda anchor: (None, None))
    monkeypatch.setattr(c, "read_latest_item", lambda: _make_item())

    bundle = c.capture_item_at_cursor()

    assert bundle is not None
    assert bundle.items[0].image is None


def test_capture_returns_none_when_no_tts_item(monkeypatch, tmp_path) -> None:
    c = _reload(monkeypatch, tmp_path)

    fake_cropped = np.zeros((4, 4, 3), dtype=np.uint8)
    monkeypatch.setattr(c, "pointer_position", lambda: (100, 200))
    monkeypatch.setattr(c, "monitor_to_window", lambda coord: coord)
    import src.giaoit.stash_scan as stash_scan_mod

    fake_detection = SimpleNamespace(found=True, cropped_descr=fake_cropped, crop_roi=None, failure_reason=None)
    monkeypatch.setattr(stash_scan_mod, "_capture_stable_tooltip", lambda anchor: (fake_detection, fake_cropped))
    monkeypatch.setattr(c, "read_latest_item", lambda: None)

    assert c.capture_item_at_cursor() is None


def test_capture_returns_none_when_pointer_fails(monkeypatch, tmp_path) -> None:
    c = _reload(monkeypatch, tmp_path)

    def raise_() -> None:
        raise RuntimeError("no pointer")

    monkeypatch.setattr(c, "pointer_position", lambda: raise_())

    assert c.capture_item_at_cursor() is None


def test_capture_returns_none_when_read_latest_item_raises(monkeypatch, tmp_path) -> None:
    c = _reload(monkeypatch, tmp_path)

    fake_cropped = np.zeros((4, 4, 3), dtype=np.uint8)
    monkeypatch.setattr(c, "pointer_position", lambda: (100, 200))
    monkeypatch.setattr(c, "monitor_to_window", lambda coord: coord)
    import src.giaoit.stash_scan as stash_scan_mod

    fake_detection = SimpleNamespace(found=True, cropped_descr=fake_cropped, crop_roi=None, failure_reason=None)
    monkeypatch.setattr(stash_scan_mod, "_capture_stable_tooltip", lambda anchor: (fake_detection, fake_cropped))

    def raise_() -> None:
        raise RuntimeError("tts broken")

    monkeypatch.setattr(c, "read_latest_item", lambda: raise_())

    assert c.capture_item_at_cursor() is None


def teardown_module(module) -> None:  # noqa: ANN001
    importlib.reload(giaoit_capture)
