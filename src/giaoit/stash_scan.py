"""Full-stash reader for GiaoIT V1 (F4 hotkey).

Mirrors the slot-iteration pattern in ``src/loot/filter.py::check_items`` and
``src/loot/orchestration.py::run_loot_filter`` but performs *no* side-effects:
no marking as junk/favorite, no dropping, no auto-use of manuals. It only reads
each item via TTS and crops the tooltip via ``find_descr_with_diagnostics``.

Scan speed is configurable via three settings in ``GeneralModel``:
  - ``scan_hover_delay_factor`` — controls Mouse.move curve speed
  - ``scan_post_hover_sleep``   — wait after hover before reading TTS
  - ``scan_inter_tab_sleep``    — wait after switching stash tabs
"""

import logging
import threading
import time

from src.automation import character_inventory, stash_inventory
from src.game_data import ItemType
from src.giaoit.models import CaptureBundle, CapturedItem
from src.item import AffixType
from src.perception import (
    capture,
    find_descr_with_diagnostics,
    latest_item_lines,
    latest_item_version,
    read_latest_item,
)
from src.settings import get_settings

LOGGER = logging.getLogger(__name__)

_ALL_GA_WARNING_RATIO = 0.8

# Module-level cancel event for the in-progress scan. ``read_full_stash`` checks
# this between slots and aborts early when set. ``handler.capture_stash_full``
# sets it when the user presses F4 again while a scan is already running —
# turning the second F4 press into a stop request instead of a no-op.
_CANCEL_EVENT = threading.Event()


def request_cancel() -> None:
    """Signal the running scan (if any) to stop after the current slot."""
    _CANCEL_EVENT.set()


def _is_cancelled() -> bool:
    return _CANCEL_EVENT.is_set()


def _reset_cancel() -> None:
    _CANCEL_EVENT.clear()


_TTS_SETTLE_POLL_SECONDS = 0.01
_TTS_SETTLE_TIMEOUT_SECONDS = 2.0
# How long the TTS buffer is allowed to keep returning the previous item before
# we conclude this slot is empty / unreadable and skip it. Generous to avoid
# missing items on slow pipes, but bounded so we don't waste the full 1.5s when
# the slot genuinely has no item.
_TTS_SETTLE_SKIP_AFTER_STALE_SECONDS = 1.0
# Two frames must agree within this histogram distance for the tooltip image to
# be considered stable. Mirrors the pattern in src/loot/highlighting_worker.py.
_TOOLTIP_STABLE_HIST_THRESHOLD = 0.90
_TOOLTIP_STABLE_DELAY_SECONDS = 0.15


def _item_signature(item) -> tuple:
    """Stable identity for an Item — excludes object identity so repeated reads
    of the same logical item produce the same signature.
    """
    return (item.item_type, item.name, item.power, tuple((a.name, a.value, a.type) for a in item.affixes))


def _snapshot_tts_lines() -> tuple[str, ...]:
    """Snapshot the raw TTS buffer as an immutable tuple for comparison."""
    try:
        return tuple(latest_item_lines())
    except Exception:
        LOGGER.debug("latest_item_lines failed; returning empty tuple", exc_info=True)
        return ()


def _wait_for_tts_update(pre_hover_version: int, slot_center: tuple[int, int], previous_signature: tuple | None):
    """Wait until the TTS publisher flushes a fresh item (``latest_item_version``
    bumps past ``pre_hover_version``), or skip/timeout.

    Earlier versions compared the parsed Item signature or the raw text buffer.
    Both broke on adjacent slots with identical content — same text meant the
    settle loop thought TTS hadn't flushed yet, even though it actually had.
    Tracking the publisher's monotonic version counter solves that: every
    ``publish_item`` call bumps the counter regardless of content, so two
    adjacent identical items still produce two distinct version bumps.

    Returns ``(item, status)``:
      - "new"       — TTS flushed a fresh payload; parse and return
      - "skip"      — no flush in the grace window; treat slot as empty
      - "timeout"   — full timeout elapsed without resolution
      - "cancelled" — user pressed F4 again
    """
    deadline = time.monotonic() + _TTS_SETTLE_TIMEOUT_SECONDS
    skip_deadline = time.monotonic() + _TTS_SETTLE_SKIP_AFTER_STALE_SECONDS
    last_lines_len = 0
    while time.monotonic() < deadline:
        if _is_cancelled():
            LOGGER.info("Scan cancelled by user (F4 pressed again)")
            return None, "cancelled"
        current_version = latest_item_version()
        if current_version != pre_hover_version:
            # TTS publisher flushed a fresh item — parse the latest buffer.
            try:
                from src.perception import parse_item_text

                item = parse_item_text(list(latest_item_lines()))
            except Exception:
                LOGGER.exception("parse_item_text failed during settle")
                return None, "timeout"
            if item is None:
                # Version bumped but parse failed — keep polling briefly in
                # case the buffer is still being filled.
                last_lines_len = sum(len(line) for line in latest_item_lines())
                time.sleep(_TTS_SETTLE_POLL_SECONDS)
                continue
            return item, "new"
        last_lines_len = sum(len(line) for line in latest_item_lines())
        if time.monotonic() > skip_deadline:
            elapsed = time.monotonic() - (skip_deadline - _TTS_SETTLE_SKIP_AFTER_STALE_SECONDS)
            LOGGER.info("Slot at %s: no TTS update after %.2fs — treating as empty", slot_center, elapsed)
            return None, "skip"
        time.sleep(_TTS_SETTLE_POLL_SECONDS)
    LOGGER.warning(
        "Slot at %s TIMEOUT after %.1fs (TTS settle full timeout). Last buffer had %d chars. "
        "If this slot had an item, TTS pipe lagged too long.",
        slot_center,
        _TTS_SETTLE_TIMEOUT_SECONDS,
        last_lines_len,
    )
    return None, "timeout"


_TOOLTIP_FIRST_FRAME_RETRIES = 6
_TOOLTIP_FIRST_FRAME_RETRY_DELAY_SECONDS = 0.08


def _capture_stable_tooltip(anchor: tuple[int, int], item_descr=None):
    """Capture the tooltip at ``anchor``. Always returns the first valid crop.

    The previous version returned ``None`` when two consecutive frames disagreed
    (likely a fade-in animation). That was too strict — it dropped ~half the
    images even though the first frame was perfectly readable. The current
    version still tries the stability check, but on disagreement it returns the
    first frame anyway: an image that is slightly mid-animation is still more
    useful than no image at all for downstream pricing.

    We also retry the first-frame detection up to ``_TOOLTIP_FIRST_FRAME_RETRIES``
    times. Some tooltip variants (notably magic-rarity two-handed weapons) take
    a few extra frames to fully render their top-left corner after hover — a
    single retry was not enough.

    When all template-matching retries fail, fall back to a content-aware fixed
    crop: use ``item_descr`` (if available) to estimate the tooltip height from
    affix/aspect counts, and choose the left/right direction based on cursor
    position (game rule: cursor on left → tooltip opens right).
    """
    try:
        # First-frame detection with retries — game may need several frames to
        # render the tooltip's top-left corner for some item types.
        first_detection = None
        first = None
        for _ in range(_TOOLTIP_FIRST_FRAME_RETRIES):
            first = capture(force_new=True)
            first_detection = find_descr_with_diagnostics(first, anchor)
            if first_detection.found and first_detection.cropped_descr is not None:
                break
            time.sleep(_TOOLTIP_FIRST_FRAME_RETRY_DELAY_SECONDS)
        if first_detection is None or not first_detection.found or first_detection.cropped_descr is None:
            # Fallback: template matching at 0.80 misses some magic-rarity items
            # (notably masterworked weapons with the *glowing*/*perpetual*
            # prefix whose top-left corner is thinner). Use content-aware crop:
            # direction from cursor position, height from item fields.
            LOGGER.info(
                "Standard tooltip detection failed at %s after %d attempts — using content-aware fallback crop",
                anchor,
                _TOOLTIP_FIRST_FRAME_RETRIES,
            )
            return _content_aware_fallback_crop(first, anchor, item_descr)
        first_crop = first_detection.cropped_descr

        time.sleep(_TOOLTIP_STABLE_DELAY_SECONDS)
        second = capture(force_new=True)
        second_detection = find_descr_with_diagnostics(second, anchor)
        if not second_detection.found or second_detection.cropped_descr is None:
            # Second frame failed entirely — accept the first frame.
            return first_detection, first_crop

        try:
            from src.perception import compare_histograms

            score = compare_histograms(first_detection.cropped_descr, second_detection.cropped_descr)
        except Exception:
            LOGGER.debug("compare_histograms unavailable; accepting first frame", exc_info=True)
            return first_detection, first_crop

        if score >= _TOOLTIP_STABLE_HIST_THRESHOLD:
            return first_detection, first_crop
        # Frames disagree but both succeeded — accept the first frame anyway.
        # A slightly mid-animation tooltip image is still useful for downstream
        # pricing; dropping it loses data we can't recover later.
        LOGGER.debug("tooltip unstable at anchor %s (score=%.3f); keeping first frame anyway", anchor, score)
        return first_detection, first_crop
    except Exception:
        LOGGER.exception("tooltip capture failed at anchor %s", anchor)
        return None, None


def _detect_tooltip_via_affix_bullet(img, anchor: tuple[int, int]):
    """Find tooltip by detecting affix bullet points when top-left corner matching fails.

    Affix bullet points (the small dot before each affix line) exist in every
    tooltip regardless of rarity — magic, rare, legendary, unique. We search
    the image for these bullets, take the cluster nearest the cursor anchor,
    and crop a region that covers the bullet cluster with generous padding for
    the item name + header above.
    """
    try:
        from src.perception import search as _search
        from src.perception.image import crop as _crop
        from src.perception.tooltip.core import DescrDetection

        h, w = img.shape[:2]
        x, y = anchor

        # Search a region around the cursor. Tooltip can open left or right,
        # up or down. Search a generous box: ±900px horizontally, ±600px vertically
        # (clamped to image bounds). At UHD these are roughly the tooltip dimensions;
        # at QHD they cover the same screen fraction.
        search_left = max(0, x - 900)
        search_top = max(0, y - 600)
        search_right = min(w, x + 900)
        search_bottom = min(h, y + 600)
        roi = [search_left, search_top, search_right - search_left, search_bottom - search_top]

        # Match multiple bullet variants (normal + greater + masterwork).
        matches: list = []
        for template_name in (
            "affix_bullet_point_1",
            "affix_bullet_point_1_medium",
            "affix_bullet_point_2",
            "affix_bullet_point_2_medium",
        ):
            try:
                res = _search(ref=template_name, inp_img=img, roi=roi, threshold=0.80, mode="all")
            except Exception:
                continue
            if res.success:
                matches.extend(res.matches)

        if not matches:
            return None, None

        # Pick the cluster of bullets nearest to the anchor (cursor sits inside
        # or next to the slot — tooltip bullets are within ~500px).
        def _dist(m) -> float:
            cx, cy = m.center
            return ((cx - x) ** 2 + (cy - y) ** 2) ** 0.5

        matches.sort(key=_dist)
        # Take the closest 8 matches — typical tooltip has 1-6 affix lines.
        nearby = matches[:8]
        if not nearby:
            return None, None

        # Bounding box of the bullet cluster. We only need the leftmost bullet
        # (to anchor the crop's left edge) and the top/bottom extents. Width is
        # derived from the standard tooltip width rather than the bullet span,
        # because affix text wraps variably.
        bx_min = min(m.center[0] for m in nearby)
        by_min = min(m.center[1] for m in nearby)
        by_max = max(m.center[1] for m in nearby)

        # Pad: item name + power header sit ~4 lines above the first bullet.
        # Each line is ~50px at UHD, ~33px at QHD. Use UI offsets when available.
        try:
            from src.settings import get_ui_coordinates

            line_h = get_ui_coordinates().offsets.item_descr_line_height
            descr_width = get_ui_coordinates().offsets.item_descr_width
            pad = get_ui_coordinates().offsets.item_descr_pad
        except Exception:
            line_h = 50
            descr_width = 780
            pad = 30

        # Padding strategy:
        #   - Top: 5 line heights above first bullet (item name + power + section
        #     header + extra slack for unique items with long names).
        #   - Bottom: 7 line heights below last bullet (aspect row + inherent
        #     affixes + codex upgrade note + flavor text + extra slack).
        #   - Right: full tooltip width from UI offsets (covers aspect text that
        #     extends past the affix bullets).
        #   - Left: 2× padding from leftmost bullet (covers bullet indent).
        crop_top = max(0, by_min - 5 * line_h - pad)
        crop_bottom = min(h, by_max + 7 * line_h + pad)
        crop_left = max(0, bx_min - pad * 2)
        crop_right = min(w, crop_left + descr_width)
        crop_w = crop_right - crop_left
        crop_h = crop_bottom - crop_top

        if crop_w <= 0 or crop_h <= 0:
            return None, None

        cropped = _crop(img, (crop_left, crop_top, crop_w, crop_h))
        LOGGER.info(
            "Tooltip located via affix bullet points near %s: %d matches, crop=(%d,%d,%d,%d)",
            anchor,
            len(nearby),
            crop_left,
            crop_top,
            crop_w,
            crop_h,
        )
        return (
            DescrDetection(found=True, cropped_descr=cropped, crop_roi=[crop_left, crop_top, crop_w, crop_h]),
            cropped,
        )
    except Exception:
        LOGGER.exception("Affix-bullet fallback detection failed at anchor %s", anchor)
        return None, None


def _content_aware_fallback_crop(img, anchor: tuple[int, int], item_descr=None):
    """Fallback when top-left-corner template matching fails.

    Strategy: locate the tooltip via affix bullet points (present in every
    tooltip regardless of rarity). If that also fails, save the full window
    screenshot so downstream review still has the data.
    """
    # Tier 1 fallback: affix bullet point detection.
    detection, crop = _detect_tooltip_via_affix_bullet(img, anchor)
    if detection is not None and crop is not None:
        return detection, crop

    # Tier 2 fallback: full screenshot.
    try:
        from src.perception.tooltip.core import DescrDetection

        LOGGER.info(
            "All tooltip detection failed at %s for item_type=%s — saving full screenshot",
            anchor,
            getattr(item_descr, "item_type", None),
        )
        return (
            DescrDetection(found=True, cropped_descr=img, crop_roi=[0, 0, int(img.shape[1]), int(img.shape[0])]),
            img,
        )
    except Exception:
        LOGGER.exception("Full-screenshot fallback failed at anchor %s", anchor)
        return None, None


def _read_one(inventory, item_slot, previous_signature: tuple | None) -> CapturedItem | None:
    """Hover one slot via ``inventory.hover_item_with_delay`` and read its item + image.

    Order of operations (matters for image quality):
      1. Snapshot the TTS publisher's version counter (used to detect flush).
      2. Hover the slot — cursor moves to slot center.
      3. Poll TTS until the version bumps past the snapshot (slot has an item)
         or the skip window elapses (slot is empty).
      4. Capture the screenshot NOW (tooltip is fully rendered because TTS
         and rendering are both driven by the same game frame).
      5. Find + stability-check the tooltip in the screenshot from step 4.
    """
    pre_hover_version = latest_item_version()
    inventory.hover_item_with_delay(item_slot)
    time.sleep(get_settings().general.scan_post_hover_sleep)

    item_descr, status = _wait_for_tts_update(pre_hover_version, item_slot.center, previous_signature)

    if item_descr is None:
        # skip or timeout — don't write a record, don't update previous_signature
        return None
    # Note: TemperManual check happens in _scan_slots so the previous_signature
    # is still updated correctly even when this slot is skipped.

    # Capture AFTER TTS settled — the tooltip is now guaranteed visible.
    # Pass item_descr so _capture_stable_tooltip can estimate tooltip height
    # from affix/aspect counts when the template-matching fallback kicks in.
    anchor = item_slot.center
    try:
        _detection, stable_crop = _capture_stable_tooltip(anchor, item_descr=item_descr)
    except Exception:
        LOGGER.exception("tooltip capture failed at anchor %s", anchor)
        return CapturedItem(item=item_descr, image=None)

    if stable_crop is None:
        LOGGER.debug(
            "no stable tooltip image at %s for item_type=%s; recording text only", anchor, item_descr.item_type
        )
    return CapturedItem(item=item_descr, image=stable_crop)


def _warn_if_advanced_tooltip_likely_off(items: list[CapturedItem]) -> None:
    """If most checked items report all affixes as Greater, Advanced Tooltip is probably off.

    Same heuristic as ``src/loot/filter.py::check_items`` lines 127-130: when the
    in-game Advanced Tooltip Information setting is disabled, TTS does not emit
    ``[min - max]`` ranges for non-GA affixes, so every affix looks like a Greater
    Affix. This directly degrades the captured data because min/max_value are None.
    """
    affixed_items = [ci for ci in items if ci.item.affixes]
    if len(affixed_items) < 3:
        return
    all_ga = [ci for ci in affixed_items if all(affix.type == AffixType.greater for affix in ci.item.affixes)]
    if len(all_ga) / len(affixed_items) > _ALL_GA_WARNING_RATIO:
        LOGGER.warning(
            "%d out of %d items had all greater affixes — Advanced Tooltip Information "
            "is probably off. Captured JSON will have min_value/max_value = None. "
            "Enable it in Options > Gameplay.",
            len(all_ga),
            len(affixed_items),
        )


def _scan_slots(inventory, slots, captured: list[CapturedItem]) -> bool:
    """Hover + read each slot via ``inventory``, appending CapturedItem objects to ``captured``.

    Returns True if completed normally, False if cancelled mid-scan.

    Note: ``slot.is_junk`` / ``slot.is_fav`` from ``get_item_slots`` are
    intentionally ignored. The upstream detection (HSV brightness on a small
    ROI) is flaky — hover tooltip glow can trip the favorite flag even when the
    user has not marked the item. For GiaoIT we want to capture everything in
    the slot regardless of in-game status, so we hover every occupied slot.
    """
    previous_signature: tuple | None = None
    for index, slot in enumerate(slots):
        if _is_cancelled():
            return False
        # Don't skip is_junk/is_fav — see docstring. Those flags are unreliable
        # and we want to capture every occupied slot for downstream pricing.
        item = _read_one(inventory, slot, previous_signature)
        if item is None:
            LOGGER.warning(
                "Slot #%d at %s produced no item — skipped silently. If this slot had an item, TTS pipe missed it.",
                index,
                slot.center,
            )
            continue
        if item.item.item_type == ItemType.TemperManual:
            LOGGER.info("Slot #%d at %s skipped: TemperManual (not tradeable)", index, slot.center)
            continue
        previous_signature = _item_signature(item.item)
        captured.append(item)
    return True


def read_full_stash() -> CaptureBundle | None:
    """Iterate every occupied slot in stash tabs AND character inventory.

    Behaviour matches the F11 loot filter's ``run_loot_filter``:
      - Stash open  → scan each configured chest tab, then character inventory
      - Stash closed → scan character inventory only

    No side effects (no junk/favorite/drop). Each item is captured with its
    cropped tooltip image; bundle kind is always "stash" because we emit a
    multi-item payload.

    Cancellable: pressing F4 again mid-scan sets the cancel event. The scan
    stops after the current slot and returns a partial bundle with whatever
    was captured so far.
    """
    _reset_cancel()
    stash = stash_inventory()
    inv = character_inventory()
    config = get_settings().general
    adv_config = get_settings().advanced_options

    captured: list[CapturedItem] = []
    tabs_scanned: list[int] = []

    stash_open = stash.is_open()
    if not stash_open and adv_config.stash_chest_coordinates is not None:
        cx, cy = adv_config.stash_chest_coordinates
        base_cx, base_cy = cx, cy
        from src.settings import get_ui_coordinates
        win_w, win_h = get_ui_coordinates().pos.window_dimensions
        if win_w > 0 and win_h > 0 and (win_w != 1920 or win_h != 1080):
            cx = int(cx * win_w / 1920)
            cy = int(cy * win_h / 1080)
        LOGGER.info("Stash closed. Moving mouse to chest at window coordinate (%d, %d) to open it", cx, cy)
        from src.automation.mouse import Mouse
        from src.perception import window_to_monitor

        # Default Cerrigar FHD stash coordinate (870, 405) uses (30, 25) randomization
        # to match the bounding box X: 840-900 and Y: 380-430.
        rand_val = (30, 25) if base_cx == 870 and base_cy == 405 else 10
        mx, my = window_to_monitor((cx, cy))
        Mouse.move(mx, my, randomize=rand_val)
        Mouse.click("left")
        time.sleep(1.0)
        stash_open = stash.is_open()
        if not stash_open:
            LOGGER.warning("Clicking stash chest did not open stash UI")

    cancelled = False

    if stash_open:
        for tab in config.check_chest_tabs:
            if _is_cancelled():
                cancelled = True
                break
            stash.switch_to_tab(tab)
            time.sleep(config.scan_inter_tab_sleep)
            tabs_scanned.append(tab)
            occupied, _ = stash.get_item_slots()
            LOGGER.info("Scanning stash tab %s: %d slots occupied", tab, len(occupied))
            if not occupied:
                # Empty tab — skip but keep scanning the rest of the configured
                # tabs. Users often have gaps (tab 1 empty while 2/3 are full),
                # so breaking early here would silently drop the contents of
                # later tabs.
                LOGGER.info("Stash tab %s is empty — skipping to next configured tab", tab)
                continue
            tab_before = len(captured)
            if not _scan_slots(stash, occupied, captured):
                cancelled = True
                break
            LOGGER.info("Stash tab %s done: %d/%d items captured", tab, len(captured) - tab_before, len(occupied))

        if not cancelled and captured:
            # Then character inventory — same as run_loot_filter does after stash.
            # Skipped when stash was empty (we don't know if inv is meaningful then).
            move_pointer_inv_to_origin()
            time.sleep(config.scan_inter_tab_sleep)
            occupied_inv, _ = inv.get_item_slots()
            LOGGER.info("Scanning character inventory: %d slots occupied", len(occupied_inv))
            if not _scan_slots(inv, occupied_inv, captured):
                cancelled = True
    else:
        if not inv.open():
            LOGGER.error("Inventory did not open; nothing to capture")
            return None
        occupied_inv, _ = inv.get_item_slots()
        LOGGER.info("Stash closed; scanning inventory: %d slots occupied", len(occupied_inv))
        if not _scan_slots(inv, occupied_inv, captured):
            cancelled = True

    if cancelled:
        LOGGER.info("Scan cancelled after %d items captured", len(captured))
        _reset_cancel()

    if not captured:
        LOGGER.warning("GiaoIT stash scan produced no items")
        return None

    if not cancelled:
        _warn_if_advanced_tooltip_likely_off(captured)

    return CaptureBundle(kind="stash", items=captured, source="f4_key", stash_tabs_scanned=tabs_scanned)


def move_pointer_inv_to_origin() -> None:
    """Move the pointer to the window origin so the next slot's hover is clean.

    Mirrors ``run_loot_filter`` between stash and inventory scans. Kept here
    rather than reusing orchestration.py to avoid importing the loot module.
    """
    try:
        from src.automation import move_pointer
        from src.perception import abs_window_to_monitor

        move_pointer(*abs_window_to_monitor((0, 0)))
    except Exception:
        LOGGER.debug("move_pointer to origin failed; continuing", exc_info=True)


def search_and_mark(search_params, callback=None) -> list:
    """Single-pass search: hover → read → match → mark as junk.

    ``search_params`` is a dict with "type" key:
      - {"type": "affix", "pool": AffixFilterCountModel}  — match affixes
      - {"type": "aspect", "name": "aspect_name"}            — match item.aspect.name
      - {"type": "name", "name": "unique_name"}              — match item.name
    """
    search_type = search_params.get("type", "affix")
    pool = search_params.get("pool")
    search_name = search_params.get("name", "")
    aspect_min = search_params.get("min_value")
    aspect_max = search_params.get("max_value")
    from src.automation import press_key, release_key

    _reset_cancel()
    stash = stash_inventory()
    inv = character_inventory()
    config = get_settings().general

    try:
        from src.item.filter.engine import Filter

        flt = Filter()
        flt._did_files_change = lambda *args, **kwargs: False
        flt.files_loaded = True
    except Exception:
        LOGGER.exception("Filter init failed")
        return []

    def _ga_check(matched, pool):
        if not matched:
            return matched
        is_or = getattr(pool, "match_mode", "all") == "any"
        for exp in pool.count:
            if not getattr(exp, "want_greater", False):
                continue
            has_name = any(getattr(a, "name", "") == exp.name for a in matched)
            if not has_name:
                if is_or:
                    continue
                return []
            has_ga = any(
                getattr(a, "name", "") == exp.name and getattr(getattr(a, "type", None), "name", "") == "greater"
                for a in matched
            )
            if not has_ga:
                return []
        return matched

    results: list[tuple] = []
    scanned = 0
    matches = 0

    def _process_slot(inv_obj, slot) -> None:
        nonlocal scanned, matches
        if _is_cancelled():
            return

        # 1. Capture version BEFORE hover. Any stale flush from the previous
        #    slot will bump version DURING the hover animation. After hover,
        #    we wait for the NEXT bump = THIS slot's item.
        pre_hover_ver = latest_item_version()

        # 2. Hover slot
        inv_obj.hover_item_with_delay(slot)
        time.sleep(get_settings().general.scan_post_hover_sleep)

        # 3. Poll for version bump = THIS slot's TTS flush
        item_descr = None
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            if _is_cancelled():
                return
            if latest_item_version() != pre_hover_ver:
                # Version bumped — could be stale flush OR new item.
                # Read and check if it's different from what we just read
                # for the previous slot.
                try:
                    item_descr = read_latest_item()
                except Exception:
                    pass
                if item_descr is not None:
                    break
            time.sleep(0.01)

        # Fallback: if no version bump in 2s, read whatever is in buffer
        if item_descr is None:
            try:
                item_descr = read_latest_item()
            except Exception:
                return

        if item_descr is None:
            return

        scanned += 1

        # ── Match check based on search type ─────────────────────────────
        item_name = item_descr.original_name or item_descr.name or str(item_descr.item_type)
        is_match = False

        if search_type == "affix" and pool is not None:
            try:
                matched = flt._match_affixes_count([pool], item_descr.affixes, 0)
            except Exception:
                matched = []
            matched = _ga_check(matched, pool)
            is_match = bool(matched)
        elif search_type == "aspect":
            aspect = item_descr.aspect
            if aspect is not None:
                name_ok = aspect.name and aspect.name.lower() == search_name.lower()
                if not name_ok:
                    is_match = False
                else:
                    is_match = True
                    if aspect_min is not None or aspect_max is not None:
                        aspect_val = aspect.value if aspect.value is not None else 0
                        # User inputs % as value/max*100 (what the game displays).
                        # VD: value=96, max=100 → 96%.  Input min=89 → 96>=89 → MATCH.
                        if aspect.max_value is not None and aspect.max_value != 0:
                            pct = 100.0 * aspect_val / aspect.max_value
                        else:
                            pct = aspect_val
                        LOGGER.info(
                            "  aspect check: %s value=%s range=[%s-%s] roll=%.1f%% (min=%s max=%s)",
                            aspect.name,
                            aspect_val,
                            aspect.min_value,
                            aspect.max_value,
                            pct,
                            aspect_min,
                            aspect_max,
                        )
                        if aspect_min is not None and pct < aspect_min:
                            is_match = False
                        if aspect_max is not None and pct > aspect_max:
                            is_match = False
        elif search_type == "name":
            item_unique_name = item_descr.name or ""
            is_match = item_unique_name and item_unique_name.lower() == search_name.lower()

        if not is_match:
            LOGGER.info("Item-search (%s): %s -> SKIP", search_type, item_name)
            return

        # MATCH — send space with press/release gap
        LOGGER.info("Item-search (%s): %s -> MATCH — marking as junk", search_type, item_name)
        try:
            # Check current slot status BEFORE marking.
            # Game cycle: normal -> junk -> favorite -> normal
            # We only want to mark as junk if the item is currently "normal"
            # (not already junk or favorite). If it's already junk, skip.
            # If it's favorite, skip (don't touch favorites).
            is_junk = getattr(slot, "is_junk", False)
            is_fav = getattr(slot, "is_fav", False)

            if is_junk:
                LOGGER.info("  -> already junk — skip")
            elif is_fav:
                # Favorite → junk cycle: space 2 lần
                # (fav → normal → junk)
                LOGGER.info("  -> was favorite, converting to junk")
                press_key("space")
                time.sleep(0.05)
                release_key("space")
                time.sleep(0.2)
                press_key("space")
                time.sleep(0.05)
                release_key("space")
                time.sleep(0.3)
            else:
                # Normal → junk: space 1 lần
                press_key("space")
                time.sleep(0.05)
                release_key("space")
                time.sleep(0.3)
        except Exception:
            LOGGER.exception("mark failed for %s", item_name)

        matches += 1
        results.append((item_descr, []))
        if callback is not None:
            callback(scanned, matches)

    stash_open = stash.is_open()
    adv_config = get_settings().advanced_options
    if not stash_open and adv_config.stash_chest_coordinates is not None:
        cx, cy = adv_config.stash_chest_coordinates
        base_cx, base_cy = cx, cy
        from src.settings import get_ui_coordinates
        win_w, win_h = get_ui_coordinates().pos.window_dimensions
        if win_w > 0 and win_h > 0 and (win_w != 1920 or win_h != 1080):
            cx = int(cx * win_w / 1920)
            cy = int(cy * win_h / 1080)
        LOGGER.info(
            "Stash closed. Moving mouse to chest at window coordinate (%d, %d) to open it for affix search", cx, cy
        )
        from src.automation.mouse import Mouse
        from src.perception import window_to_monitor

        # Default Cerrigar FHD stash coordinate (870, 405) uses (30, 25) randomization
        # to match the bounding box X: 840-900 and Y: 380-430.
        rand_val = (30, 25) if base_cx == 870 and base_cy == 405 else 10
        mx, my = window_to_monitor((cx, cy))
        Mouse.move(mx, my, randomize=rand_val)
        Mouse.click("left")
        time.sleep(1.0)
        stash_open = stash.is_open()
        if not stash_open:
            LOGGER.warning("Clicking stash chest did not open stash UI")

    LOGGER.info("Affix-search config: tabs=%s stash_open=%s", config.check_chest_tabs, stash_open)

    if stash_open:
        for tab in config.check_chest_tabs:
            if _is_cancelled():
                break
            stash.switch_to_tab(tab)
            time.sleep(config.scan_inter_tab_sleep)
            occupied, _ = stash.get_item_slots()
            LOGGER.info("Affix-search tab %s: %d slots", tab, len(occupied))
            for slot in occupied:
                _process_slot(stash, slot)

    LOGGER.info("Affix-search done: %d/%d items matched", matches, scanned)
    return results
