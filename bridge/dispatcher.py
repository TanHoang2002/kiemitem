"""Dispatcher — turns a new pending JSON file into a sendable job.

Pipeline:
  1. Read the JSON payload from disk.
  2. Collect sibling image files referenced by items[].image_file.
  3. For kind=single: invoke the confirm UI hook (set by main loop).
  4. For kind=stash: send straight away with a synthetic account_id.
  5. Send the payload to the receiver.
  6. Move files to sent/ on success, hand off to retry queue on retryable
     failure, or move to failed/ on non-retryable failure.
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from bridge.accounts import load_accounts
from bridge.config import BridgeConfig
from bridge.log import get_logger
from bridge.mover import move_to_failed, move_to_sent
from bridge.retry_queue import RetryQueue
from bridge.sender import SendResult, send_payload

LOGGER = get_logger()
STASH_ACCOUNT_FALLBACK = "auto-stash"


class Dispatcher:
    def __init__(
        self,
        config: BridgeConfig,
        retry_queue: RetryQueue,
        confirm_fn: Callable[[dict[str, Any], list[Path]], str | None] | None = None,
    ) -> None:
        self._config = config
        self._retry_queue = retry_queue
        self._confirm_fn = confirm_fn
        self._accounts = load_accounts()

    def reload_accounts(self) -> None:
        self._accounts = load_accounts()

    def accounts(self) -> list[str]:
        return list(self._accounts)

    def handle(self, json_path: Path) -> None:
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except OSError, json.JSONDecodeError:
            LOGGER.exception("failed to parse %s; moving to failed", json_path)
            move_to_failed(json_path.stem, json_path, [], self._config.failed_dir)
            return

        capture_id = payload.get("capture_id")
        kind = payload.get("kind")
        if not isinstance(capture_id, str) or kind not in {"single", "stash", "currency"}:
            LOGGER.error("invalid payload at %s (capture_id=%r kind=%r)", json_path, capture_id, kind)
            move_to_failed(json_path.stem, json_path, [], self._config.failed_dir)
            return

        image_paths = self._collect_image_paths(json_path.parent, payload)

        account_id: str | None
        if kind == "single":
            account_id = self._confirm_or_default(payload, image_paths)
            if account_id is None:
                LOGGER.info("user dismissed capture %s; moving to failed", capture_id)
                move_to_failed(capture_id, json_path, image_paths, self._config.failed_dir)
                return
        else:
            account_id = payload.get("account_id") or (self._accounts[0] if self._accounts else STASH_ACCOUNT_FALLBACK)

        self._send_or_retry(capture_id, json_path, image_paths, payload, account_id)

    def handle_retry(self, entry: dict[str, Any]) -> None:
        capture_id = entry["capture_id"]
        json_path = Path(entry["json_path"])
        image_paths = [Path(p) for p in entry["image_paths"]]
        account_id = entry.get("account_id") or STASH_ACCOUNT_FALLBACK

        if not json_path.exists():
            LOGGER.warning("retry entry %s points to missing file; dropping", capture_id)
            self._retry_queue.remove(capture_id)
            return

        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except OSError, json.JSONDecodeError:
            LOGGER.exception("retry payload unreadable; dropping %s", capture_id)
            self._retry_queue.remove(capture_id)
            move_to_failed(capture_id, json_path, image_paths, self._config.failed_dir)
            return

        self._send_or_retry(capture_id, json_path, image_paths, payload, account_id)

    def _send_or_retry(
        self, capture_id: str, json_path: Path, image_paths: list[Path], payload: dict[str, Any], account_id: str
    ) -> None:
        result: SendResult = send_payload(
            self._config.receiver_url, payload, image_paths, account_id, api_key=self._config.api_key
        )
        if result.ok:
            LOGGER.info("capture %s sent (deduped=%s status=%s)", capture_id, result.deduped, result.status_code)
            self._retry_queue.remove(capture_id)
            move_to_sent(capture_id, json_path, image_paths, self._config.sent_dir)
            return

        if not result.retryable:
            LOGGER.error(
                "capture %s failed permanently (status=%s error=%s)", capture_id, result.status_code, result.error
            )
            self._retry_queue.remove(capture_id)
            move_to_failed(capture_id, json_path, image_paths, self._config.failed_dir)
            return

        LOGGER.warning(
            "capture %s retryable failure (status=%s error=%s); enqueuing", capture_id, result.status_code, result.error
        )
        bumped = self._retry_queue.record_failure(
            capture_id, result.error or "unknown", self._config.backoff_base_seconds, self._config.backoff_max_seconds
        )
        if not bumped:
            self._retry_queue.add(
                capture_id=capture_id,
                json_path=json_path,
                image_paths=image_paths,
                account_id=account_id,
                kind=payload.get("kind", "single"),
            )
            self._retry_queue.record_failure(
                capture_id,
                result.error or "unknown",
                self._config.backoff_base_seconds,
                self._config.backoff_max_seconds,
            )

    def _collect_image_paths(self, root: Path, payload: dict[str, Any]) -> list[Path]:
        out: list[Path] = []
        for item in payload.get("items", []):
            image_file = item.get("image_file")
            if not isinstance(image_file, str):
                continue
            candidate = root / image_file
            if candidate.exists():
                out.append(candidate)
        return out

    def _confirm_or_default(self, payload: dict[str, Any], image_paths: list[Path]) -> str | None:
        if self._confirm_fn is not None:
            try:
                return self._confirm_fn(payload, image_paths)
            except Exception:
                LOGGER.exception("confirm UI raised; treating as dismissed")
                return None
        if not self._accounts:
            LOGGER.warning("no accounts loaded and no confirm hook; using %s", STASH_ACCOUNT_FALLBACK)
            return STASH_ACCOUNT_FALLBACK
        return self._accounts[0]
