"""Minimal string-map i18n for the bridge (Tkinter UI).

The bridge runs in its own process and cannot import ``src.i18n`` without
pulling in PyQt and the entire d4lf tree. This standalone module keeps the
same semantics: ``tr(key)`` looks up the active language; missing keys fall
back to the key itself.

Language is read from ``GIAOIT_LANGUAGE`` (default ``enUS``) to avoid
re-implementing the d4lf params loader here.
"""

import os

_STRINGS_EN = {
    "Capture": "Capture",
    "(no preview)": "(no preview)",
    "(no image)": "(no image)",
    "Parsed item (editable before send):": "Parsed item (editable before send):",
    "Account:": "Account:",
    "Send": "Send",
    "Dismiss": "Dismiss",
    "No account": "No account",
    "Pick or type an account first.": "Pick or type an account first.",
    "GiaoIT Bridge": "GiaoIT Bridge",
}

_STRINGS_VI = {
    "Capture": "Bản chụp",
    "(no preview)": "(không xem trước)",
    "(no image)": "(không ảnh)",
    "Parsed item (editable before send):": "Món đã parse (có thể sửa trước khi gửi):",
    "Account:": "Tài khoản:",
    "Send": "Gửi",
    "Dismiss": "Bỏ qua",
    "No account": "Chưa chọn tài khoản",
    "Pick or type an account first.": "Chọn hoặc nhập tài khoản trước.",
    "GiaoIT Bridge": "Cầu nối GiaoIT",
}

_CATALOGS = {"enUS": _STRINGS_EN, "viVN": _STRINGS_VI}


def _current_language() -> str:
    lang = os.environ.get("GIAOIT_LANGUAGE", "enUS")
    return lang if lang in _CATALOGS else "enUS"


def tr(key: str) -> str:
    if not isinstance(key, str) or not key:
        return key
    return _CATALOGS.get(_current_language(), _STRINGS_EN).get(key, key)
