"""Tests for src.giaoit.stash_scan.read_full_stash."""

import importlib
from types import SimpleNamespace

import numpy as np

from src.game_data import ItemRarity, ItemType
from src.giaoit import stash_scan as giaoit_stash_scan
from src.item import Affix, AffixType, Item


def _reload(monkeypatch, tmp_path):
    monkeypatch.setenv("GIAOIT_CAPTURE_DIR", str(tmp_path))
    importlib.reload(giaoit_stash_scan)
    return giaoit_stash_scan


def _slot(center=(10, 10), is_junk=False, is_fav=False):
    return SimpleNamespace(center=center, is_junk=is_junk, is_fav=is_fav)


def _fake_inventory(slots):
    """Build a fake inventory-like object whose hover_item_with_delay is a no-op."""
    inv = SimpleNamespace()
    inv.hover_item_with_delay = lambda _slot: None
    inv.get_item_slots = lambda: (slots, [])
    inv.open = lambda: True
    inv.is_open = lambda: True
    inv.switch_to_tab = lambda _tab: None
    return inv


def _make_item(item_type=ItemType.Helm) -> Item:
    return Item(item_type=item_type, power=900, rarity=ItemRarity.Legendary,
                affixes=[Affix(name="armor", value=1.0, type=AffixType.normal)])


def _fake_general(**overrides) -> SimpleNamespace:
    """Build a GeneralModel-shaped SimpleNamespace including scan-speed settings."""
    defaults = {
        "check_chest_tabs": [0],
        "scan_post_hover_sleep": 0.0,
        "scan_inter_tab_sleep": 0.0,
        "scan_hover_delay_factor": (1.0, 1.5),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_read_full_stash_returns_bundle_when_stash_open(monkeypatch, tmp_path) -> None:
    s = _reload(monkeypatch, tmp_path)

    slot1 = _slot(center=(10, 10))
    slot2 = _slot(center=(20, 20))
    stash = _fake_inventory([slot1, slot2])
    stash.is_open = lambda: True
    inv = _fake_inventory([])
    inv.is_open = lambda: False
    inv.open = lambda: False

    monkeypatch.setattr(s, "stash_inventory", lambda: stash)
    monkeypatch.setattr(s, "character_inventory", lambda: inv)
    monkeypatch.setattr(s, "get_settings", lambda: SimpleNamespace(general=_fake_general()))
    monkeypatch.setattr(s.time, "sleep", lambda _s: None)
    monkeypatch.setattr(s, "capture", lambda *args, **kwargs: np.zeros((4, 4, 3), dtype=np.uint8))

    # Simulate TTS buffer flush: each call returns a different raw text tuple
    # so the snapshot diff triggers and parse_item_text returns the next item.
    item_a = _make_item()
    item_b = _make_item(ItemType.Gloves)
    parse_iter = iter([item_a, item_b])
    version_iter = iter([0, 1, 1, 2])
    monkeypatch.setattr(s, "latest_item_lines", lambda: ("line",))
    monkeypatch.setattr(s, "latest_item_version", lambda: next(version_iter))
    import src.perception as _perception_mod
    monkeypatch.setattr(_perception_mod, "parse_item_text", lambda lines: next(parse_iter))

    detection = SimpleNamespace(found=True, cropped_descr=np.zeros((2, 2, 3), dtype=np.uint8), failure_reason=None)
    monkeypatch.setattr(s, "find_descr_with_diagnostics", lambda img, anchor: detection)

    bundle = s.read_full_stash()

    assert bundle is not None
    assert bundle.kind == "stash"
    assert bundle.source == "f4_key"
    assert bundle.stash_tabs_scanned == [0]
    assert len(bundle.items) == 2
    assert bundle.items[0].item is item_a
    assert bundle.items[1].item is item_b


def test_read_full_stash_captures_junk_and_favorite_slots(monkeypatch, tmp_path) -> None:
    """GiaoIT scans every occupied slot — is_junk/is_fav flags are ignored
    because upstream detection is flaky (hover glow can trigger false positives).
    """
    s = _reload(monkeypatch, tmp_path)

    slot_junk = _slot(is_junk=True)
    slot_fav = _slot(is_fav=True)
    slot_real = _slot()
    stash = _fake_inventory([slot_junk, slot_fav, slot_real])
    stash.is_open = lambda: True
    inv = _fake_inventory([])
    inv.is_open = lambda: False
    inv.open = lambda: False

    monkeypatch.setattr(s, "stash_inventory", lambda: stash)
    monkeypatch.setattr(s, "character_inventory", lambda: inv)
    monkeypatch.setattr(s, "get_settings", lambda: SimpleNamespace(general=_fake_general()))
    monkeypatch.setattr(s.time, "sleep", lambda _s: None)
    monkeypatch.setattr(s, "capture", lambda *args, **kwargs: np.zeros((4, 4, 3), dtype=np.uint8))

    item_a = _make_item()
    item_b = _make_item()
    item_c = _make_item()
    parse_iter = iter([item_a, item_b, item_c])
    version_iter = iter([0, 1, 1, 2, 2, 3])
    monkeypatch.setattr(s, "latest_item_lines", lambda: ("line",))
    monkeypatch.setattr(s, "latest_item_version", lambda: next(version_iter))
    import src.perception as _perception_mod
    monkeypatch.setattr(_perception_mod, "parse_item_text", lambda lines: next(parse_iter))
    detection = SimpleNamespace(found=True, cropped_descr=None, failure_reason=None)
    monkeypatch.setattr(s, "find_descr_with_diagnostics", lambda img, anchor: detection)

    bundle = s.read_full_stash()

    assert bundle is not None
    # All 3 slots captured — junk/fav flags ignored
    assert len(bundle.items) == 3


def test_read_full_stash_falls_back_to_inventory(monkeypatch, tmp_path) -> None:
    s = _reload(monkeypatch, tmp_path)

    slot_inv = _slot()
    stash = SimpleNamespace(is_open=lambda: False)
    inv = _fake_inventory([slot_inv])
    inv.is_open = lambda: True
    inv.open = lambda: True

    monkeypatch.setattr(s, "stash_inventory", lambda: stash)
    monkeypatch.setattr(s, "character_inventory", lambda: inv)
    monkeypatch.setattr(s.time, "sleep", lambda _s: None)
    monkeypatch.setattr(s, "capture", lambda *args, **kwargs: np.zeros((4, 4, 3), dtype=np.uint8))

    item = _make_item()
    tts_buffer_iter = iter([(), ("line_a",)])
    parse_iter = iter([item])
    version_iter = iter([0, 1])
    monkeypatch.setattr(s, "latest_item_lines", lambda: next(tts_buffer_iter))
    monkeypatch.setattr(s, "latest_item_version", lambda: next(version_iter))
    import src.perception as _perception_mod
    monkeypatch.setattr(_perception_mod, "parse_item_text", lambda lines: next(parse_iter))
    detection = SimpleNamespace(found=True, cropped_descr=None, failure_reason=None)
    monkeypatch.setattr(s, "find_descr_with_diagnostics", lambda img, anchor: detection)

    bundle = s.read_full_stash()

    assert bundle is not None
    assert bundle.kind == "stash"
    assert bundle.stash_tabs_scanned == []


def test_read_full_stash_returns_none_when_no_items(monkeypatch, tmp_path) -> None:
    s = _reload(monkeypatch, tmp_path)

    stash = _fake_inventory([])
    stash.is_open = lambda: True
    inv = _fake_inventory([])
    inv.is_open = lambda: False
    inv.open = lambda: False

    monkeypatch.setattr(s, "stash_inventory", lambda: stash)
    monkeypatch.setattr(s, "character_inventory", lambda: inv)
    monkeypatch.setattr(s, "get_settings", lambda: SimpleNamespace(general=_fake_general()))
    monkeypatch.setattr(s.time, "sleep", lambda _s: None)

    assert s.read_full_stash() is None


def test_read_one_does_not_call_junk_or_favorite_actions(monkeypatch, tmp_path) -> None:
    """Critical V1 requirement: stash scan has zero side-effects."""
    s = _reload(monkeypatch, tmp_path)

    from src.loot import colors as loot_colors

    junk_calls = []
    fav_calls = []
    drop_calls = []
    monkeypatch.setattr(loot_colors, "mark_as_junk", lambda: junk_calls.append(1))
    monkeypatch.setattr(loot_colors, "mark_as_favorite", lambda: fav_calls.append(1))
    monkeypatch.setattr(loot_colors, "drop_item_from_inventory", lambda: drop_calls.append(1))

    slot = _slot()
    stash = _fake_inventory([slot])
    stash.is_open = lambda: True
    inv = _fake_inventory([])
    inv.is_open = lambda: False
    inv.open = lambda: False

    monkeypatch.setattr(s, "stash_inventory", lambda: stash)
    monkeypatch.setattr(s, "character_inventory", lambda: inv)
    monkeypatch.setattr(s, "get_settings", lambda: SimpleNamespace(general=_fake_general()))
    monkeypatch.setattr(s.time, "sleep", lambda _t: None)
    monkeypatch.setattr(s, "capture", lambda *args, **kwargs: np.zeros((4, 4, 3), dtype=np.uint8))

    item = _make_item()
    tts_buffer_iter = iter([(), ("line_a",)])
    parse_iter = iter([item])
    version_iter = iter([0, 1])
    monkeypatch.setattr(s, "latest_item_lines", lambda: next(tts_buffer_iter))
    monkeypatch.setattr(s, "latest_item_version", lambda: next(version_iter))
    import src.perception as _perception_mod
    monkeypatch.setattr(_perception_mod, "parse_item_text", lambda lines: next(parse_iter))
    detection = SimpleNamespace(found=True, cropped_descr=None, failure_reason=None)
    monkeypatch.setattr(s, "find_descr_with_diagnostics", lambda img, anchor: detection)

    s.read_full_stash()

    assert junk_calls == []
    assert fav_calls == []
    assert drop_calls == []


def test_empty_stash_tab_continues_to_next_tab(monkeypatch, tmp_path) -> None:
    """Empty tabs are skipped but later tabs are still scanned."""
    s = _reload(monkeypatch, tmp_path)

    # Tab 0 empty, tab 1 has one item, tab 2 empty.
    # The fake stash get_item_slots returns the slot list passed in, then []
    # when called again — we make it cycle: [] → [slot] → [].
    slot_tab1 = _slot(center=(100, 100))
    inv_slot = _slot(center=(1, 1))

    tab_yields = iter([[slot_tab1]])  # only one tab worth of slots

    class _TabCyclingStash:
        is_open = staticmethod(lambda: True)

        def switch_to_tab(self, _tab):
            return None

        def __init__(self):
            self._calls = 0

        def get_item_slots(self):
            # Tab 0: empty; Tab 1: slot; Tab 2: empty.
            results = [[], [slot_tab1], []]
            slots = results[self._calls % 3]
            self._calls += 1
            return (slots, [])

        def hover_item_with_delay(self, _slot):
            return None

    stash = _TabCyclingStash()
    inv = _fake_inventory([])  # inventory empty so no extra slot scan
    inv.is_open = lambda: True
    inv.open = lambda: True

    monkeypatch.setattr(s, "stash_inventory", lambda: stash)
    monkeypatch.setattr(s, "character_inventory", lambda: inv)
    monkeypatch.setattr(s, "get_settings", lambda: SimpleNamespace(general=_fake_general(check_chest_tabs=[0, 1, 2])))
    monkeypatch.setattr(s.time, "sleep", lambda _t: None)
    monkeypatch.setattr(s, "capture", lambda *args, **kwargs: np.zeros((4, 4, 3), dtype=np.uint8))

    item = _make_item()
    parse_iter = iter([item])
    # version sequence: tab 0 hover-snapshot=0, slot 1 on tab 1 bumps=1
    version_iter = iter([0, 0, 0, 1, 1])
    monkeypatch.setattr(s, "latest_item_lines", lambda: ("line",))
    monkeypatch.setattr(s, "latest_item_version", lambda: next(version_iter))
    import src.perception as _perception_mod
    monkeypatch.setattr(_perception_mod, "parse_item_text", lambda lines: next(parse_iter))
    detection = SimpleNamespace(found=True, cropped_descr=None, failure_reason=None)
    monkeypatch.setattr(s, "find_descr_with_diagnostics", lambda img, anchor: detection)

    bundle = s.read_full_stash()

    # Empty tab 0 must NOT short-circuit: tab 1 still scanned.
    assert bundle is not None
    assert bundle.stash_tabs_scanned == [0, 1, 2]
    assert len(bundle.items) >= 1


def teardown_module(module) -> None:
    importlib.reload(giaoit_stash_scan)
