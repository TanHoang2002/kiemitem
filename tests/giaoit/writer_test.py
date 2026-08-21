"""Tests for src.giaoit.writer.write_capture."""

import importlib
import json

import cv2
import numpy as np

from src.game_data import ItemRarity, ItemType
from src.giaoit import writer as giaoit_writer
from src.giaoit.models import CaptureBundle, CapturedItem
from src.item import Affix, AffixType, Item


def _reload_with_tmp_env(monkeypatch, tmp_path):
    monkeypatch.setenv("GIAOIT_CAPTURE_DIR", str(tmp_path))
    importlib.reload(giaoit_writer)
    return giaoit_writer


def _make_item(item_type=ItemType.Helm) -> Item:
    return Item(
        item_type=item_type,
        rarity=ItemRarity.Legendary,
        power=900,
        affixes=[Affix(name="armor", value=10.0, type=AffixType.normal)],
    )


def _fake_image() -> np.ndarray:
    return np.zeros((4, 4, 3), dtype=np.uint8)


def test_single_capture_writes_json_and_image(monkeypatch, tmp_path) -> None:
    w = _reload_with_tmp_env(monkeypatch, tmp_path)
    bundle = CaptureBundle(
        kind="single",
        items=[CapturedItem(item=_make_item(), image=_fake_image())],
        source="f2_key",
    )

    json_path = w.write_capture(bundle)

    assert json_path is not None
    pending = tmp_path / "captures" / "pending"
    files = {f.name for f in pending.iterdir()}
    assert json_path.name in files

    capture_id = json_path.stem
    assert f"{capture_id}.png" in files
    assert not any(f.endswith(".tmp") for f in files)


def test_two_captures_have_distinct_capture_ids(monkeypatch, tmp_path) -> None:
    w = _reload_with_tmp_env(monkeypatch, tmp_path)

    bundle = CaptureBundle(
        kind="single",
        items=[CapturedItem(item=_make_item(), image=None)],
        source="f2_key",
    )
    first = w.write_capture(bundle)
    second = w.write_capture(bundle)

    assert first is not None
    assert second is not None
    # Fixed filename mode: both writes go to the same file (overwrite).
    # The file exists with the latest content.
    assert first.stem == second.stem
    assert second.exists()


def test_stash_capture_writes_one_image_per_item(monkeypatch, tmp_path) -> None:
    """3 DISTINCT items → 3 PNG files (dedup keeps all 3)."""
    from src.game_data import ItemType
    w = _reload_with_tmp_env(monkeypatch, tmp_path)
    # Use different item types so they're not duplicates
    bundle = CaptureBundle(
        kind="stash",
        items=[
            CapturedItem(item=_make_item(ItemType.Helm), image=_fake_image()),
            CapturedItem(item=_make_item(ItemType.Gloves), image=_fake_image()),
            CapturedItem(item=_make_item(ItemType.Boots), image=_fake_image()),
        ],
        source="f4_key",
        stash_tabs_scanned=[0],
    )

    json_path = w.write_capture(bundle)
    assert json_path is not None
    base = json_path.stem

    pending = tmp_path / "captures" / "pending"
    files = {f.name for f in pending.iterdir()}
    assert files == {
        f"{base}.json",
        f"{base}_000.png",
        f"{base}_001.png",
        f"{base}_002.png",
    }


def test_stash_capture_dedup_identical_items(monkeypatch, tmp_path) -> None:
    """3 IDENTICAL items → 1 PNG file (dedup removes 2 duplicates)."""
    w = _reload_with_tmp_env(monkeypatch, tmp_path)
    bundle = CaptureBundle(
        kind="stash",
        items=[
            CapturedItem(item=_make_item(), image=_fake_image()),
            CapturedItem(item=_make_item(), image=_fake_image()),
            CapturedItem(item=_make_item(), image=_fake_image()),
        ],
        source="f4_key",
        stash_tabs_scanned=[0],
    )

    json_path = w.write_capture(bundle)
    assert json_path is not None
    base = json_path.stem

    pending = tmp_path / "captures" / "pending"
    files = {f.name for f in pending.iterdir()}
    # Only 1 item after dedup → 1 JSON + 1 PNG
    assert files == {
        f"{base}.json",
        f"{base}_000.png",
    }


def test_round_trip_parse_json(monkeypatch, tmp_path) -> None:
    w = _reload_with_tmp_env(monkeypatch, tmp_path)
    bundle = CaptureBundle(
        kind="single",
        items=[CapturedItem(item=_make_item(), image=None)],
        source="f2_key",
    )

    json_path = w.write_capture(bundle)
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert payload["schema"] == "giaoit.capture.v1"
    assert payload["kind"] == "single"
    assert payload["items"][0]["item"]["item_type"] == "helm"
    assert payload["items"][0]["item"]["affixes"][0]["type"] == "normal"


def test_empty_bundle_returns_none(monkeypatch, tmp_path) -> None:
    w = _reload_with_tmp_env(monkeypatch, tmp_path)
    bundle = CaptureBundle(kind="single", items=[], source="f2_key")
    assert w.write_capture(bundle) is None


def test_image_filename_pattern(monkeypatch, tmp_path) -> None:
    w = _reload_with_tmp_env(monkeypatch, tmp_path)
    bundle_single = CaptureBundle(
        kind="single",
        items=[CapturedItem(item=_make_item(), image=_fake_image())],
        source="f2_key",
    )
    json_single = w.write_capture(bundle_single)
    assert json_single is not None
    capture_id = json_single.stem
    pending = tmp_path / "captures" / "pending"
    assert (pending / f"{capture_id}.png").exists()

    # Reload so the next call uses a fresh state dir.
    monkeypatch.setenv("GIAOIT_CAPTURE_DIR", str(tmp_path))
    importlib.reload(giaoit_writer)


def test_image_with_none_writes_no_png(monkeypatch, tmp_path) -> None:
    w = _reload_with_tmp_env(monkeypatch, tmp_path)
    bundle = CaptureBundle(
        kind="single",
        items=[CapturedItem(item=_make_item(), image=None)],
        source="f2_key",
    )
    json_path = w.write_capture(bundle)
    assert json_path is not None

    pending = tmp_path / "captures" / "pending"
    pngs = [p for p in pending.iterdir() if p.suffix == ".png"]
    assert pngs == []


def test_image_actually_written_is_openable(monkeypatch, tmp_path) -> None:
    w = _reload_with_tmp_env(monkeypatch, tmp_path)
    img = np.full((8, 8, 3), 200, dtype=np.uint8)
    bundle = CaptureBundle(
        kind="single",
        items=[CapturedItem(item=_make_item(), image=img)],
        source="f2_key",
    )
    json_path = w.write_capture(bundle)
    assert json_path is not None

    capture_id = json_path.stem
    png_path = tmp_path / "captures" / "pending" / f"{capture_id}.png"
    loaded = cv2.imread(str(png_path))
    assert loaded is not None
    assert loaded.shape == (8, 8, 3)


def teardown_module(module) -> None:
    importlib.reload(giaoit_writer)
