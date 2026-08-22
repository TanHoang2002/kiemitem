"""Public interface for the string-map i18n layer."""

from src.i18n.catalog import available_languages, current_language, set_language_override, tr

__all__ = ["available_languages", "current_language", "set_language_override", "tr"]
