"""Filesystem watcher for ~/.giaoit/captures/pending/.

Uses ``watchdog`` if available (event-driven), with a polling fallback for
tests / restricted environments. The watcher is responsible for the
"stability" check: a file must be unchanged for ``stability_seconds`` before
it is queued for processing. This avoids racing against the tool's
``.tmp`` -> ``os.replace`` atomic write.
"""

import threading
import time
from collections.abc import Callable
from pathlib import Path

from bridge.config import BridgeConfig
from bridge.log import get_logger

LOGGER = get_logger()


class PollingWatcher:
    """Polling fallback — robust on every platform, simple, no extra deps at runtime."""

    def __init__(self, config: BridgeConfig, on_new_file: Callable[[Path], None]) -> None:
        self._config = config
        self._on_new_file = on_new_file
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        # path -> (mtime_when_first_seen, monotonic_when_first_seen)
        self._seen: dict[Path, tuple[float, float]] = {}

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, daemon=True, name="giaoit-watcher")
        self._thread.start()
        LOGGER.info("PollingWatcher started on %s", self._config.pending_dir)

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def scan_once(self) -> list[Path]:
        """Single scan pass. Returns the list of newly-stable files. Tests call this directly."""
        if not self._config.pending_dir.exists():
            return []
        now_mono = time.monotonic()
        ready: list[Path] = []
        for path in sorted(self._config.pending_dir.glob("*.json")):
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            record = self._seen.get(path)
            if record is None:
                self._seen[path] = (mtime, now_mono)
                continue
            recorded_mtime, recorded_at = record
            if mtime != recorded_mtime:
                # File was rewritten — restart the stability window.
                self._seen[path] = (mtime, now_mono)
                continue
            if now_mono - recorded_at < self._config.stability_seconds:
                continue
            ready.append(path)
            self._seen.pop(path, None)
        return ready

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                ready = self.scan_once()
                for path in ready:
                    try:
                        self._on_new_file(path)
                    except Exception:
                        LOGGER.exception("dispatcher raised on %s", path)
            except Exception:
                LOGGER.exception("scan pass crashed")
            self._stop.wait(self._config.poll_interval_seconds)


def build_watcher(config: BridgeConfig, on_new_file: Callable[[Path], None]) -> PollingWatcher:
    """Factory used by main.py. Always returns the polling watcher for portability."""
    return PollingWatcher(config, on_new_file)
