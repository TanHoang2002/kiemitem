"""Persistent retry queue — survives bridge restarts.

Stored as a JSON array under ``~/.giaoit/state/retry_queue.json``. Each entry:

    {
        "capture_id": "...",
        "json_path": "/path/to/pending/<capture_id>.json",
        "image_paths": ["/path/to/pending/<capture_id>.png", ...],
        "account_id": "acc1" | null,
        "kind": "single" | "stash",
        "retry_count": 0,
        "next_attempt_at": "2026-08-12T00:00:00+00:00",
        "last_error": null
    }
"""

import json
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from bridge.log import get_logger

LOGGER = get_logger()


def _now() -> datetime:
    return datetime.now(tz=UTC)


class RetryQueue:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._entries: list[dict[str, Any]] = self._load()

    def _load(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except OSError, json.JSONDecodeError:
            LOGGER.exception("retry_queue unreadable at %s; starting empty", self._path)
            return []

    def _persist(self) -> None:
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._entries, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._path)

    def add(self, capture_id: str, json_path: Path, image_paths: list[Path], account_id: str | None, kind: str) -> None:
        entry = {
            "capture_id": capture_id,
            "json_path": str(json_path),
            "image_paths": [str(p) for p in image_paths],
            "account_id": account_id,
            "kind": kind,
            "retry_count": 0,
            "next_attempt_at": _now().isoformat(timespec="milliseconds"),
            "last_error": None,
        }
        with self._lock:
            if any(e["capture_id"] == capture_id for e in self._entries):
                LOGGER.info("retry_queue already has %s; not re-adding", capture_id)
                return
            self._entries.append(entry)
            self._persist()

    def remove(self, capture_id: str) -> None:
        with self._lock:
            before = len(self._entries)
            self._entries = [e for e in self._entries if e["capture_id"] != capture_id]
            if len(self._entries) != before:
                self._persist()

    def record_failure(self, capture_id: str, error: str, backoff_base: float, backoff_max: float) -> bool:
        """Bump retry count and return True if entry should still be retried."""
        with self._lock:
            for entry in self._entries:
                if entry["capture_id"] != capture_id:
                    continue
                entry["retry_count"] += 1
                entry["last_error"] = error
                delay = min(backoff_base * (2 ** (entry["retry_count"] - 1)), backoff_max)
                entry["next_attempt_at"] = (_now() + timedelta(seconds=delay)).isoformat(timespec="milliseconds")
                self._persist()
                return True
            return False

    def due(self, max_retries: int) -> list[dict[str, Any]]:
        now = _now()
        out: list[dict[str, Any]] = []
        with self._lock:
            for entry in self._entries:
                if entry["retry_count"] >= max_retries:
                    continue
                try:
                    due_at = datetime.fromisoformat(entry["next_attempt_at"])
                except ValueError:
                    due_at = now
                if due_at <= now:
                    out.append(dict(entry))
        return out

    def exhausted(self, max_retries: int) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(e) for e in self._entries if e["retry_count"] >= max_retries]

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)
