"""Write a capture bundle to disk: JSON payload + cropped tooltip PNG.

Single-file mode: each capture kind writes to a FIXED filename and overwrites
the previous capture of the same kind. Old PNG files from the previous capture
are deleted first so the directory stays clean.

* single: ``latest_single.json`` and ``latest_single.png``
* stash:  ``latest_stash.json`` and ``latest_stash_<NNN>.png`` per item
"""

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

import cv2

from src.giaoit.config import machine_id
from src.giaoit.encoder import build_payload, item_hash
from src.giaoit.models import CaptureBundle, CaptureMeta
from src.giaoit.paths import pending_dir

LOGGER = logging.getLogger(__name__)

_FIXED_NAMES = {"single": "latest_single", "stash": "latest_stash", "currency": "latest_currency"}


def _new_meta(fixed_id: str) -> CaptureMeta:
    return CaptureMeta(
        capture_id=fixed_id,
        captured_at=datetime.now(tz=UTC).isoformat(timespec="milliseconds"),
        machine_id=machine_id(),
    )


def _image_filename(base: str, kind: str, index: int) -> str:
    if kind == "single":
        return f"{base}.png"
    return f"{base}_{index:03d}.png"


def _assign_image_filenames(bundle: CaptureBundle, base: str) -> None:
    for index, captured in enumerate(bundle.items):
        if captured.image is None:
            captured.image_file = None
            continue
        captured.image_file = _image_filename(base, bundle.kind, index)


def _write_json_atomic(payload: dict[str, object], target: Path) -> None:
    tmp = target.with_name(f".{target.name}.tmp")
    with tmp.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2, ensure_ascii=False)
        fp.write("\n")
    Path(tmp).replace(target)


def _write_image(image, target: Path) -> None:
    tmp = target.with_name(f".{target.stem}.tmp.png")
    ok = cv2.imwrite(str(tmp), image)
    if not ok:
        LOGGER.warning("cv2.imwrite reported failure for %s", target)
    Path(tmp).replace(target)


def _cleanup_old_files(pending: Path, base: str) -> None:
    """Delete old JSON + PNG files from the previous capture of this kind."""
    for old_file in pending.glob(f"{base}*"):
        try:
            old_file.unlink()
        except OSError:
            LOGGER.debug("Could not delete old file %s", old_file)


def _dedup_items(items: list) -> list:
    """Remove duplicate items (same content) from a list, keeping the first occurrence."""
    seen: set[str] = set()
    unique: list = []
    for captured in items:
        orig_name = str(captured.item.original_name or "")
        # If it has a stack number (like "(1000)"), it is a stackable currency item, so we always keep it
        if "(" in orig_name and ")" in orig_name:
            unique.append(captured)
            continue

        try:
            digest = item_hash(captured.item)
        except Exception:
            digest = str(id(captured))  # fallback: keep if hash fails
        if digest not in seen:
            seen.add(digest)
            unique.append(captured)
    if len(unique) < len(items):
        LOGGER.info(
            "Dedup: %d items → %d unique (%d duplicates removed)", len(items), len(unique), len(items) - len(unique)
        )
    return unique


def _is_currency_item(item) -> bool:
    orig_name = str(item.original_name or "").lower()
    name = str(item.name or "").lower()

    if "lair" in orig_name or "lair" in name:
        return True
    if "root" in orig_name or "root" in name:
        return True
    if "crux" in orig_name or "crux" in name:
        return True
    if "grand" in orig_name or "grand" in name:
        return True
    if ("flawless" in orig_name and "horadric" in orig_name) or ("flawless" in name and "horadric" in name):
        return True
    return False


def write_capture(bundle: CaptureBundle, account_id: str | None = None, request_id: str | None = None) -> Path | None:
    """Persist bundle to ``pending/`` with a FIXED filename (overwrites previous)."""
    if not bundle.items:
        LOGGER.warning("write_capture called with empty bundle; skipping")
        return None

    # Dedup: remove items with identical content (same affixes, power, type, ...)
    bundle.items = _dedup_items(bundle.items)

    # Strip images for currency items to prevent unnecessary image transmission
    for captured in bundle.items:
        if _is_currency_item(captured.item):
            captured.image = None
            captured.image_file = None

    if not bundle.items:
        LOGGER.warning("All items were duplicates; nothing to write")
        return None

    base = _FIXED_NAMES.get(bundle.kind, "latest_capture")
    pending = pending_dir()

    # Delete old files from previous capture of this kind
    _cleanup_old_files(pending, base)

    # Use a fresh UUID for capture_id (dedup) but FIXED filename
    meta = _new_meta(uuid.uuid4().hex)
    _assign_image_filenames(bundle, base)

    json_path = pending / f"{base}.json"

    try:
        for captured in bundle.items:
            if captured.image is None or captured.image_file is None:
                continue
            _write_image(captured.image, pending / captured.image_file)

        payload = build_payload(bundle, meta)
        if account_id:
            payload["account_id"] = account_id
        if request_id:
            payload["request_id"] = request_id
        _write_json_atomic(payload, json_path)
    except Exception:
        LOGGER.exception("Failed to write capture %s", meta.capture_id)
        return None

    LOGGER.info("GiaoIT capture written: %s (kind=%s, items=%d)", json_path, bundle.kind, len(bundle.items))
    return json_path
