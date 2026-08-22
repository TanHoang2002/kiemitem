"""HTTP client that posts a captured payload to the receiver.

Status mapping:
  200 OK (deduped)  -> success
  201 Created       -> success
  4xx               -> non-retryable; caller should move to failed/
  5xx / network     -> retryable; caller records a failure and backs off
"""

import json
from pathlib import Path
from typing import Any

import httpx

from bridge.log import get_logger

LOGGER = get_logger()


class SendResult:
    def __init__(self, ok: bool, deduped: bool, retryable: bool, status_code: int | None, error: str | None) -> None:
        self.ok = ok
        self.deduped = deduped
        self.retryable = retryable
        self.status_code = status_code
        self.error = error

    def __repr__(self) -> str:
        return (
            f"SendResult(ok={self.ok}, deduped={self.deduped}, retryable={self.retryable}, "
            f"status_code={self.status_code}, error={self.error!r})"
        )


def send_payload(
    receiver_url: str, payload: dict[str, Any], image_paths: list[Path], account_id: str, timeout_seconds: float = 30.0
) -> SendResult:
    files: list[tuple[str, tuple[str, bytes, str]]] = []
    for path in image_paths:
        try:
            files.append(("images", (path.name, path.read_bytes(), "image/png")))
        except OSError:
            LOGGER.warning("failed to read image %s; skipping", path)

    data = {"payload": json.dumps(payload, ensure_ascii=False), "account_id": account_id}

    try:
        response = httpx.post(f"{receiver_url}/items", data=data, files=files, timeout=timeout_seconds)
    except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPError) as exc:
        return SendResult(ok=False, deduped=False, retryable=True, status_code=None, error=str(exc))

    if response.status_code in (200, 201):
        try:
            body = response.json()
        except ValueError:
            body = {}
        return SendResult(
            ok=True, deduped=bool(body.get("deduped")), retryable=False, status_code=response.status_code, error=None
        )

    retryable = response.status_code >= 500
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = response.text
    return SendResult(ok=False, deduped=False, retryable=retryable, status_code=response.status_code, error=str(detail))
