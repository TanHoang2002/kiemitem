"""Tests for src.giaoit.config."""

import importlib

from src.giaoit import config as giaoit_config


def test_machine_id_generates_and_persists(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GIAOIT_CAPTURE_DIR", str(tmp_path))
    importlib.reload(giaoit_config)
    giaoit_config.reset_cache_for_tests()

    first = giaoit_config.machine_id()
    second = giaoit_config.machine_id()

    assert first == second
    assert (tmp_path / "machine_id").read_text(encoding="utf-8").strip() == first


def test_machine_id_reads_existing_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GIAOIT_CAPTURE_DIR", str(tmp_path))
    importlib.reload(giaoit_config)
    giaoit_config.reset_cache_for_tests()

    fixed = "deadbeefcafe1234"
    (tmp_path / "machine_id").write_text(fixed + "\n", encoding="utf-8")
    assert giaoit_config.machine_id() == fixed


def test_kill_switch_active_for_truthy_values(monkeypatch) -> None:
    for truthy in ("1", "true", "TRUE", "yes", "on"):
        monkeypatch.setenv("GIAOIT_DISABLED", truthy)
        assert giaoit_config.is_kill_switch_active() is True


def test_kill_switch_inactive_for_falsy_values(monkeypatch) -> None:
    for falsy in ("", "0", "no", "off", "anything-else"):
        monkeypatch.setenv("GIAOIT_DISABLED", falsy)
        assert giaoit_config.is_kill_switch_active() is False


def test_is_capture_enabled_returns_false_when_kill_switch_set(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GIAOIT_CAPTURE_DIR", str(tmp_path))
    monkeypatch.setenv("GIAOIT_DISABLED", "1")
    importlib.reload(giaoit_config)

    assert giaoit_config.is_capture_enabled() is False


def test_is_capture_enabled_reads_general_setting(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GIAOIT_CAPTURE_DIR", str(tmp_path))
    monkeypatch.delenv("GIAOIT_DISABLED", raising=False)
    importlib.reload(giaoit_config)

    from types import SimpleNamespace

    import src.settings as settings_mod

    fake_settings = SimpleNamespace(general=SimpleNamespace(capture_mode=True))
    monkeypatch.setattr(settings_mod, "get_settings", lambda: fake_settings)

    assert giaoit_config.is_capture_enabled() is True


def teardown_module(module) -> None:
    importlib.reload(giaoit_config)
