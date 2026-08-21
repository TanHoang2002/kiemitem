"""Tests for src.i18n.en — basic shape checks."""

from src.i18n.en import STRINGS_EN


def test_en_catalog_is_non_empty() -> None:
    assert len(STRINGS_EN) > 50


def test_en_keys_match_values_identity() -> None:
    """In English, key == value so fallback is transparent."""
    mismatches = [k for k, v in STRINGS_EN.items() if k != v]
    assert mismatches == [], f"en values should equal keys, mismatches: {mismatches[:5]}"


def test_en_has_core_settings_keys() -> None:
    for key in ("Settings", "Save", "Cancel", "OK"):
        assert key in STRINGS_EN
