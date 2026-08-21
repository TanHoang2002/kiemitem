"""Tests for src.i18n.vi — parity with en."""

from src.i18n.en import STRINGS_EN
from src.i18n.vi import STRINGS_VI


def test_vi_catalog_is_non_empty() -> None:
    assert len(STRINGS_VI) > 50


def test_vi_keys_match_en_keys_exactly() -> None:
    """Every key in en must exist in vi and vice versa."""
    en_keys = set(STRINGS_EN)
    vi_keys = set(STRINGS_VI)
    missing_in_vi = en_keys - vi_keys
    extra_in_vi = vi_keys - en_keys
    assert not missing_in_vi, f"keys missing in vi: {sorted(missing_in_vi)[:10]}"
    assert not extra_in_vi, f"keys in vi but not in en: {sorted(extra_in_vi)[:10]}"


def test_vi_values_differ_from_en_for_core_keys() -> None:
    """Translation should actually translate — not copy the English string."""
    not_translated = [k for k in ("Settings", "Save", "Cancel") if STRINGS_VI[k] == STRINGS_EN[k]]
    assert not_translated == [], f"values identical to en: {not_translated}"
