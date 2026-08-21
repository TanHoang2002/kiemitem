"""Single-item capture at the current cursor (F2 hotkey).

Unlike the per-slot loop in ``src/loot/filter.py``, this runs once: grab a
screenshot, locate the tooltip at the cursor position, parse the TTS-read
item, and bundle them together for the writer.

Reuses ``_capture_stable_tooltip`` from ``stash_scan`` to get retry + fallback
behaviour for tooltip variants that the upstream template matching misses
(notably magic-rarity items with thin top-left corners).
"""

import logging
from typing import TYPE_CHECKING

from src.automation import pointer_position
from src.giaoit.models import CaptureBundle, CapturedItem
from src.perception import capture, monitor_to_window, read_latest_item

if TYPE_CHECKING:
    from src.item.models import Item

LOGGER = logging.getLogger(__name__)


def _anchor_at_cursor() -> tuple[int, int] | None:
    try:
        monitor_xy = pointer_position()
    except Exception:
        LOGGER.exception("Failed to read pointer position")
        return None
    try:
        win_xy = monitor_to_window(monitor_xy)
    except Exception:
        LOGGER.exception("Failed to convert pointer position to window coordinates")
        return None
    try:
        return int(win_xy[0]), int(win_xy[1])
    except Exception:
        LOGGER.exception("Invalid window coordinates from %s", win_xy)
        return None


def _read_item() -> Item | None:
    try:
        return read_latest_item()
    except Exception:
        LOGGER.exception("read_latest_item raised; treating as no item")
        return None


def capture_item_at_cursor() -> CaptureBundle | None:
    """Capture the item currently under the cursor.

    Returns None if anything goes wrong — callers should not crash the hotkey
    thread on capture failures.
    """
    anchor = _anchor_at_cursor()
    if anchor is None:
        return None

    # Lazy import to avoid circular dependency (stash_scan imports capture's
    # _anchor_at_cursor/_read_item at module level via runner).
    from src.giaoit.stash_scan import _capture_stable_tooltip

    try:
        _detection, cropped = _capture_stable_tooltip(anchor)
    except Exception:
        LOGGER.exception("tooltip capture failed at anchor %s", anchor)
        cropped = None
    if cropped is None:
        LOGGER.warning(
            "No tooltip image captured at cursor anchor %s — recording item text only",
            anchor,
        )

    item = _read_item()
    if item is None:
        LOGGER.warning("No TTS item text available; cannot capture")
        return None

    return CaptureBundle(
        kind="single",
        items=[CapturedItem(item=item, image=cropped)],
        source="f2_key",
    )
