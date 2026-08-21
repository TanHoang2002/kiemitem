"""Smoke test for the public surface of src.i18n."""

import src.i18n as i18n


def test_public_symbols_importable() -> None:
    assert callable(i18n.tr)
    assert callable(i18n.current_language)
    assert callable(i18n.set_language_override)
    assert callable(i18n.available_languages)
    assert "enUS" in i18n.available_languages()
    assert "viVN" in i18n.available_languages()
