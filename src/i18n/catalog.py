"""String-map i18n: ``tr(key)`` looks up the current language catalog.

Languages are stored as flat dicts in :mod:`src.i18n.en` and
:mod:`src.i18n.vi`. The active language is read from
``general.language`` on every call (cheap — the settings loader caches).
If the key is missing for the active language, the key itself is returned
unchanged so the UI falls back to English — no crash, no broken layout.
"""

import logging

from src.i18n.en import STRINGS_EN
from src.i18n.vi import STRINGS_VI
from src.settings import get_settings

LOGGER = logging.getLogger(__name__)

_CATALOGS = {"enUS": STRINGS_EN, "viVN": STRINGS_VI}

_override_language: str | None = None


def available_languages() -> list[str]:
    return sorted(_CATALOGS.keys())


def current_language() -> str:
    if _override_language is not None:
        return _override_language
    try:
        lang = get_settings().general.language
    except Exception:
        LOGGER.debug("settings unavailable; defaulting to enUS")
        return "enUS"
    return lang if lang in _CATALOGS else "enUS"


def set_language_override(lang: str | None) -> None:
    """Test-only: force a language without touching settings."""
    global _override_language
    if lang is not None and lang not in _CATALOGS:
        msg = f"unknown language: {lang}"
        raise ValueError(msg)
    _override_language = lang


def tr(key: str) -> str:
    """Return the translated string, falling back to ``key`` on miss."""
    if not isinstance(key, str) or not key:
        return key
    catalog = _CATALOGS.get(current_language(), STRINGS_EN)
    value = catalog.get(key)
    if value is None:
        return key
    return value
