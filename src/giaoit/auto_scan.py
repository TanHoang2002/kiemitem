"""Auto-scan: subscribe to TTS events and capture items as the user hovers them.

Wires into ``Publisher().subscribe_item`` once at app startup. The callback
must return quickly because the TTS publisher dispatches synchronously on the
TTS reader thread (see ``src/perception/listener.py``). Heavy work — capture,
hash, JSON/PNG write — happens on a short-lived worker thread.

Dedup: each unique ``item_hash`` is captured at most once per session. The hash
set is in-memory only; restart resets it so the user can re-capture later with
fresh screenshots.
"""

import logging
import threading
from typing import TYPE_CHECKING

from src.giaoit.config import is_capture_enabled
from src.giaoit.encoder import item_hash
from src.giaoit.models import CaptureBundle, CapturedItem

if TYPE_CHECKING:
    from src.item.models import Item

LOGGER = logging.getLogger(__name__)

_DEDUP_TTL_SECONDS = 5.0


class AutoScanner:
    """Singleton hook subscribed to TTS events."""

    _instance: "AutoScanner | None" = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> "AutoScanner":
        with cls._instance_lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._init_state()
                cls._instance = instance
            return cls._instance

    def _init_state(self) -> None:
        self._lock = threading.RLock()
        self._seen_hashes: set[str] = set()
        self._last_hash: str | None = None
        self._last_hash_at: float = 0.0
        self._active = False
        self._filter_running = False

    # ── public API ──────────────────────────────────────────────────────────

    def activate(self) -> None:
        """Subscribe to TTS events if capture is enabled and not yet active."""
        if not is_capture_enabled():
            return
        with self._lock:
            if self._active:
                return
            try:
                from src.perception.listener import Publisher

                Publisher().subscribe_item(self._on_tts)
                self._active = True
                LOGGER.info("GiaoIT auto-scan activated")
            except Exception:
                LOGGER.exception("Failed to subscribe auto-scan to TTS publisher")

    def deactivate(self) -> None:
        """Unsubscribe from TTS events."""
        with self._lock:
            if not self._active:
                return
            try:
                from src.perception.listener import Publisher

                Publisher().unsubscribe_item(self._on_tts)
            except Exception:
                LOGGER.exception("Failed to unsubscribe auto-scan from TTS publisher")
            self._active = False
            self._seen_hashes.clear()
            self._last_hash = None
            LOGGER.info("GiaoIT auto-scan deactivated")

    def set_filter_running(self, running: bool) -> None:
        """Tell the scanner whether the loot filter is currently iterating items.

        When the filter is running it captures items itself via
        ``_maybe_capture_item``; auto-scan defers to avoid double writes.
        """
        with self._lock:
            self._filter_running = running

    def reset_for_tests() -> None:  # type: ignore[override]
        """Tests only — wipe the singleton state."""
        with AutoScanner._instance_lock:
            if AutoScanner._instance is not None:
                AutoScanner._instance.deactivate()
            AutoScanner._instance = None

    # ── TTS callback (runs on TTS thread — must return fast) ────────────────

    def _on_tts(self, _event: object) -> None:
        with self._lock:
            if not self._active or self._filter_running:
                return

        try:
            import src.perception as perception

            item_descr = perception.read_latest_item()
        except Exception:
            LOGGER.exception("auto-scan: read_latest_item raised")
            return

        if item_descr is None:
            return

        try:
            digest = item_hash(item_descr)
        except Exception:
            LOGGER.exception("auto-scan: item_hash raised")
            return

        import time

        now = time.monotonic()
        with self._lock:
            if digest in self._seen_hashes:
                return
            if digest == self._last_hash and (now - self._last_hash_at) < _DEDUP_TTL_SECONDS:
                return
            self._seen_hashes.add(digest)
            self._last_hash = digest
            self._last_hash_at = now

        # Heavy work on a daemon thread so we don't block the TTS reader.
        threading.Thread(
            target=self._capture_async,
            args=(item_descr, digest),
            daemon=True,
            name="giaoit-auto-scan",
        ).start()

    def _capture_async(self, item_descr: Item, digest: str) -> None:
        try:
            from src.giaoit.capture import _anchor_at_cursor, _read_item  # reuse helpers
            from src.perception import capture, find_descr_with_diagnostics
            from src.giaoit.writer import write_capture

            anchor = _anchor_at_cursor()
            if anchor is None:
                LOGGER.debug("auto-scan: no anchor for hash %s", digest[:8])
                return
            try:
                img = capture(force_new=True)
            except TypeError:
                img = capture()
            try:
                detection = find_descr_with_diagnostics(img, anchor)
            except Exception:
                LOGGER.exception("auto-scan: find_descr failed")
                detection = None
            cropped = detection.cropped_descr if detection and detection.found else None

            bundle = CaptureBundle(
                kind="single",
                items=[CapturedItem(item=item_descr, image=cropped)],
                source="auto_scan",
            )
            path = write_capture(bundle)
            if path is not None:
                LOGGER.info("auto-scan captured %s -> %s", digest[:8], path.name)
        except Exception:
            LOGGER.exception("auto-scan async capture failed for hash %s", digest[:8])


def get_auto_scanner() -> AutoScanner:
    """Module-level accessor — always returns the singleton."""
    return AutoScanner()


def refresh_subscription() -> None:
    """Sync the subscription state with the current settings.

    Called by ``ScriptHandler`` when ``general.capture_auto_scan`` changes.
    """
    scanner = get_auto_scanner()
    try:
        from src.settings import get_settings

        enabled = bool(get_settings().general.capture_auto_scan) and is_capture_enabled()
    except Exception:
        LOGGER.exception("auto-scan: failed to read settings; deactivating")
        scanner.deactivate()
        return

    if enabled:
        scanner.activate()
    else:
        scanner.deactivate()
