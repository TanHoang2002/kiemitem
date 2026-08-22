"""Tests for src.giaoit.auto_scan.AutoScanner."""

import importlib
from types import SimpleNamespace

import src.giaoit.auto_scan as giaoit_auto_scan
from src.game_data import ItemRarity, ItemType
from src.giaoit.auto_scan import AutoScanner
from src.item import Affix, AffixType, Item


def _reload(monkeypatch, tmp_path):
    monkeypatch.setenv("GIAOIT_CAPTURE_DIR", str(tmp_path))
    importlib.reload(giaoit_auto_scan)
    return giaoit_auto_scan


def _make_item() -> Item:
    return Item(
        item_type=ItemType.Helm,
        rarity=ItemRarity.Legendary,
        power=900,
        affixes=[Affix(name="armor", value=1.0, type=AffixType.normal)],
    )


def test_singleton_returns_same_instance() -> None:
    a = AutoScanner()
    b = AutoScanner()
    assert a is b


def test_on_tts_skips_when_inactive(monkeypatch, tmp_path) -> None:
    m = _reload(monkeypatch, tmp_path)
    AutoScanner.reset_for_tests()  # type: ignore[misc]
    scanner = m.AutoScanner()

    scanner._on_tts(None)

    assert scanner._seen_hashes == set()


def test_on_tts_dedupes_same_item(monkeypatch, tmp_path) -> None:
    m = _reload(monkeypatch, tmp_path)
    AutoScanner.reset_for_tests()  # type: ignore[misc]
    scanner = m.AutoScanner()
    scanner._active = True

    import src.perception as perception_mod

    calls: list = []
    monkeypatch.setattr(perception_mod, "read_latest_item", lambda: _make_item())
    monkeypatch.setattr(m.threading, "Thread", lambda **kw: calls.append(kw) or SimpleNamespace(start=lambda: None))

    scanner._on_tts(None)
    scanner._on_tts(None)
    scanner._on_tts(None)

    # Same item hash → only first call should spawn a worker thread
    assert len(calls) == 1


def test_on_tts_defers_when_filter_running(monkeypatch, tmp_path) -> None:
    m = _reload(monkeypatch, tmp_path)
    AutoScanner.reset_for_tests()  # type: ignore[misc]
    scanner = m.AutoScanner()
    scanner._active = True
    scanner.set_filter_running(True)

    import src.perception as perception_mod

    calls: list = []
    monkeypatch.setattr(perception_mod, "read_latest_item", lambda: _make_item())
    monkeypatch.setattr(m.threading, "Thread", lambda **kw: calls.append(kw) or SimpleNamespace(start=lambda: None))

    scanner._on_tts(None)

    assert calls == []
    assert scanner._seen_hashes == set()


def test_on_tts_handles_read_failure(monkeypatch, tmp_path) -> None:
    m = _reload(monkeypatch, tmp_path)
    AutoScanner.reset_for_tests()  # type: ignore[misc]
    scanner = m.AutoScanner()
    scanner._active = True

    def raise_() -> None:
        raise RuntimeError("tts broken")

    import src.perception as perception_mod

    monkeypatch.setattr(perception_mod, "read_latest_item", lambda: raise_())

    scanner._on_tts(None)
    assert scanner._seen_hashes == set()


def test_on_tts_ignores_none_item(monkeypatch, tmp_path) -> None:
    m = _reload(monkeypatch, tmp_path)
    AutoScanner.reset_for_tests()  # type: ignore[misc]
    scanner = m.AutoScanner()
    scanner._active = True

    import src.perception as perception_mod

    monkeypatch.setattr(perception_mod, "read_latest_item", lambda: None)

    scanner._on_tts(None)
    assert scanner._seen_hashes == set()


def test_refresh_subscription_deactivates_when_disabled(monkeypatch, tmp_path) -> None:
    m = _reload(monkeypatch, tmp_path)
    AutoScanner.reset_for_tests()  # type: ignore[misc]
    scanner = m.AutoScanner()
    scanner._active = True

    fake_settings = SimpleNamespace(general=SimpleNamespace(capture_auto_scan=False))
    monkeypatch.setattr(m, "is_capture_enabled", lambda: True)

    import src.settings as settings_mod

    monkeypatch.setattr(settings_mod, "get_settings", lambda: fake_settings)

    m.refresh_subscription()
    assert scanner._active is False


def teardown_module(module) -> None:
    importlib.reload(giaoit_auto_scan)
