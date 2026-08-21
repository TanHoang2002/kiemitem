"""In-memory idempotent storage for the receiver stub.

For V1 we keep everything in RAM but also dump each received record to
``~/.giaoit/received/<capture_id>.json`` so the trials checklist (V1 §6) can
inspect them directly.
"""

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _default_received_dir() -> Path:
    return Path.home() / ".giaoit" / "received"


def _extract_currencies(payload: dict[str, Any]) -> dict[str, int]:
    import re
    from collections import Counter
    counts = Counter()
    items_list = payload.get("items", [])
    for item_entry in items_list:
        item = item_entry.get("item", {})
        orig_name = str(item.get("original_name", "")).lower()
        name = str(item.get("name", "")).lower()
        
        match = re.search(r"\((\d+)\)", orig_name)
        quantity = int(match.group(1)) if match else 1
        
        if "greater lair" in orig_name or "greater lair" in name:
            counts["Greater Lair Key"] += quantity
        elif "lair" in orig_name or "lair" in name:
            if "greater" not in orig_name and "superior" not in orig_name:
                counts["Lair Key"] += quantity
        elif "superior" in orig_name or "superior" in name:
            counts["Superior Lair Key"] += quantity
        elif "root" in orig_name or "root" in name:
            counts["Corrupted Roots"] += quantity
        elif "crux" in orig_name or "crux" in name:
            counts["Crux of the False Prophet"] += quantity
        elif "grand" in orig_name or "grand" in name:
            gem_type = next((g for g in ["skull", "ruby", "sapphire", "topaz", "emerald", "diamond", "amethyst"] if g in orig_name), "other")
            counts[f"Grand {gem_type.capitalize()}"] += quantity
        elif ("flawless" in orig_name and "horadric" in orig_name) or ("flawless" in name and "horadric" in name):
            gem_type = next((g for g in ["skull", "ruby", "sapphire", "topaz", "emerald", "diamond", "amethyst"] if g in orig_name), "other")
            counts[f"Flawless {gem_type.capitalize()}"] += quantity
    return dict(counts)


class Storage:
    """Thread-safe dict keyed by ``capture_id`` with disk mirror."""

    def __init__(self, received_dir: Path | None = None) -> None:
        self._records: dict[str, dict[str, Any]] = {}
        self._hash_index: dict[str, str] = {}  # item_hash → capture_id (single-kind dedup)
        self._history: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._received_dir = received_dir or _default_received_dir()
        self._received_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing records from disk for persistence
        for f in self._received_dir.glob("*.json"):
            if f.name == "warehouse_history.json":
                continue
            try:
                record = json.loads(f.read_text(encoding="utf-8"))
                capture_id = record.get("capture_id")
                if capture_id:
                    self._records[capture_id] = record
                    item_hash_value = record.get("item_hash")
                    if item_hash_value:
                        self._hash_index[item_hash_value] = capture_id
            except Exception:
                continue
                
        # Load warehouse history
        history_file = self._received_dir / "warehouse_history.json"
        if history_file.exists():
            try:
                self._history = json.loads(history_file.read_text(encoding="utf-8"))
            except Exception:
                self._history = []

    def _save_history_to_disk(self) -> None:
        try:
            target = self._received_dir / "warehouse_history.json"
            target.write_text(json.dumps(self._history, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def put(
        self, capture_id: str, payload: dict[str, Any], account_id: str
    ) -> tuple[dict[str, Any], bool, bool]:
        """Insert or return existing.

        Returns ``(record, deduped_by_capture_id, deduped_by_hash)``. Only one
        of the dedup flags is True at a time. ``deduped_by_hash`` triggers when
        a different ``capture_id`` already exists for the same ``item_hash``
        (i.e. same item content captured twice).
        """
        with self._lock:
            existing = self._records.get(capture_id)
            if existing is not None:
                return existing, True, False

            item_hash_value = payload.get("item_hash") if payload.get("kind") == "single" else None
            if isinstance(item_hash_value, str) and item_hash_value:
                existing_by_hash_id = self._hash_index.get(item_hash_value)
                if existing_by_hash_id is not None and existing_by_hash_id in self._records:
                    return self._records[existing_by_hash_id], False, True

            # If kind is stash, compute differences from the latest stash of the same account_id
            if payload.get("kind") == "stash":
                new_counts = _extract_currencies(payload)
                
                # Find the latest stash record for this account_id
                latest_stash = None
                for rec in self._records.values():
                    if rec.get("kind") == "stash" and rec.get("account_id") == account_id:
                        if latest_stash is None or rec.get("received_at", "") > latest_stash.get("received_at", ""):
                            latest_stash = rec
                            
                if latest_stash is not None:
                    old_counts = _extract_currencies(latest_stash.get("payload", {}))
                    all_keys = set(new_counts.keys()) | set(old_counts.keys())
                    for key in all_keys:
                        old_qty = old_counts.get(key, 0)
                        new_qty = new_counts.get(key, 0)
                        diff = new_qty - old_qty
                        if diff != 0:
                            history_entry = {
                                "timestamp": datetime.now(tz=UTC).isoformat(timespec="seconds"),
                                "account_id": account_id,
                                "item_name": key,
                                "difference": diff,
                                "old_qty": old_qty,
                                "new_qty": new_qty
                            }
                            self._history.insert(0, history_entry)
                    self._save_history_to_disk()

            record: dict[str, Any] = {
                "capture_id": capture_id,
                "received_at": datetime.now(tz=UTC).isoformat(timespec="milliseconds"),
                "account_id": account_id,
                "items_count": len(payload.get("items", [])),
                "kind": payload.get("kind"),
                "source": payload.get("source"),
                "machine_id": payload.get("machine_id"),
                "captured_at": payload.get("captured_at"),
                "item_hash": item_hash_value,
                "payload": payload,
            }
            self._records[capture_id] = record
            if item_hash_value:
                self._hash_index[item_hash_value] = capture_id
            self._dump_to_disk(record)
            return record, False, False

    def get(self, capture_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._records.get(capture_id)

    def get_history(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._history)

    def count(self) -> int:
        with self._lock:
            return len(self._records)

    def _dump_to_disk(self, record: dict[str, Any]) -> None:
        try:
            target = self._received_dir / f"{record['capture_id']}.json"
            target.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass


_store: Storage | None = None


def get_store() -> Storage:
    global _store
    if _store is None:
        _store = Storage()
    return _store


def reset_for_tests(received_dir: Path | None = None) -> Storage:
    """Tests only — replace the global store with a fresh one."""
    global _store
    _store = Storage(received_dir=received_dir) if received_dir else Storage()
    return _store
