"""Tests for src.i18n.catalog."""

from src.i18n import catalog as i18n_catalog
from src.i18n.catalog import current_language, set_language_override, tr


def teardown_module() -> None:
    """Reset override so other tests start from a clean state."""
    set_language_override(None)


def test_tr_returns_value_for_enUS_when_override_enUS() -> None:
    set_language_override("enUS")
    assert tr("Settings") == "Settings"


def test_tr_returns_value_for_viVN_when_override_viVN() -> None:
    set_language_override("viVN")
    assert tr("Settings") == "Cài đặt"


def test_tr_falls_back_to_key_when_missing() -> None:
    set_language_override("viVN")
    assert tr("nonexistent key 12345") == "nonexistent key 12345"


def test_tr_handles_empty_and_non_string_keys() -> None:
    set_language_override("viVN")
    assert tr("") == ""
    assert tr(None) is None  # type: ignore[arg-type]


def test_current_language_uses_override() -> None:
    set_language_override("viVN")
    assert current_language() == "viVN"
    set_language_override("enUS")
    assert current_language() == "enUS"


def test_set_language_override_rejects_unknown() -> None:
    import pytest

    with pytest.raises(ValueError, match="unknown language"):
        set_language_override("frFR")


def test_available_languages_lists_both() -> None:
    langs = i18n_catalog.available_languages()
    assert "enUS" in langs
    assert "viVN" in langs
