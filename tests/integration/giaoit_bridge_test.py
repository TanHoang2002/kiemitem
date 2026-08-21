"""End-to-end integration: drop file -> bridge dispatches -> receiver stores.

These tests stand up the receiver (FastAPI TestClient) and the bridge
dispatcher against a temp ``~/.giaoit`` directory, then verify:

  * single kind round-trips and lands in sent/
  * duplicate capture_id is deduped (V1 trial #5)
  * receiver 5xx triggers retry instead of failure
  * stash kind skips confirm UI
  * .tmp partial files are ignored by the polling watcher
"""

import importlib
import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bridge import accounts as bridge_accounts
from bridge import config as bridge_config
from bridge import dispatcher as bridge_dispatcher
from bridge import retry_queue as bridge_retry_queue
from bridge import watcher as bridge_watcher
from receiver import main as receiver_main
from receiver import storage as receiver_storage


@pytest.fixture
def iso_env(tmp_path, monkeypatch):
    monkeypatch.setenv("GIAOIT_CAPTURE_DIR", str(tmp_path))
    monkeypatch.setenv("GIAOIT_RECEIVER_URL", "http://testserver")
    importlib.reload(bridge_config)
    importlib.reload(bridge_accounts)
    importlib.reload(bridge_dispatcher)
    importlib.reload(bridge_watcher)
    importlib.reload(bridge_retry_queue)
    cfg = bridge_config.load_config()
    for path in (
        cfg.pending_dir,
        cfg.sent_dir,
        cfg.failed_dir,
        cfg.received_dir,
        cfg.logs_dir,
        cfg.state_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)
    return cfg


@pytest.fixture
def client(iso_env, monkeypatch):
    """FastAPI TestClient wired to a fresh receiver store under the temp dir."""
    monkeypatch.setattr(receiver_storage, "_default_received_dir", lambda: iso_env.received_dir)
    receiver_storage.reset_for_tests(received_dir=iso_env.received_dir)
    receiver_main.START_TIME = time.monotonic()
    test_client = TestClient(receiver_main.app)

    # Route bridge.sender.send_payload via the in-process TestClient so the
    # bridge doesn't try to open a real HTTP connection to http://testserver.
    from bridge import sender as bridge_sender

    def _fake_send(receiver_url, payload, image_paths, account_id, timeout_seconds=30.0):
        import json as _json

        files = []
        for path in image_paths:
            if path.exists():
                files.append(("images", (path.name, path.read_bytes(), "image/png")))
        data = {"payload": _json.dumps(payload, ensure_ascii=False), "account_id": account_id}
        response = test_client.post("/items", data=data, files=files)
        if response.status_code in (200, 201):
            body = response.json()
            return bridge_sender.SendResult(
                ok=True,
                deduped=bool(body.get("deduped")),
                retryable=False,
                status_code=response.status_code,
                error=None,
            )
        retryable = response.status_code >= 500
        try:
            detail = response.json().get("detail")
        except ValueError:
            detail = response.text
        return bridge_sender.SendResult(
            ok=False,
            deduped=False,
            retryable=retryable,
            status_code=response.status_code,
            error=str(detail),
        )

    monkeypatch.setattr(bridge_dispatcher, "send_payload", _fake_send)
    return test_client


def _make_payload(capture_id: str, kind: str = "single", items: int = 1) -> dict:
    return {
        "schema": "giaoit.capture.v1",
        "kind": kind,
        "capture_id": capture_id,
        "captured_at": "2026-08-12T00:00:00+00:00",
        "machine_id": "m1",
        "source": "f2_key" if kind == "single" else "f4_key",
        "items": [
            {"image_file": f"{capture_id}_{i:03d}.png" if kind == "stash" else f"{capture_id}.png", "item": {"item_type": "helm"}}
            for i in range(items)
        ],
    }


def _write_capture(capture_dir: Path, payload: dict, with_images: bool = True) -> tuple[Path, list[Path]]:
    json_path = capture_dir / f"{payload['capture_id']}.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    images: list[Path] = []
    if with_images:
        for item in payload["items"]:
            name = item["image_file"]
            if name is None:
                continue
            img = capture_dir / name
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
            images.append(img)
    return json_path, images


def test_single_capture_round_trip(iso_env, client) -> None:
    dispatcher = bridge_dispatcher.Dispatcher(
        config=iso_env,
        retry_queue=bridge_retry_queue.RetryQueue(iso_env.retry_queue_file),
        confirm_fn=lambda payload, images: "acc1",
    )

    json_path, images = _write_capture(iso_env.pending_dir, _make_payload("cap-single"))
    dispatcher.handle(json_path)

    # Pending is now empty
    assert not json_path.exists()
    for img in images:
        assert not img.exists()

    # Sent dir has the bundle
    sent_bundle = iso_env.sent_dir / "cap-single"
    assert sent_bundle.exists()
    assert (sent_bundle / "payload.json").exists()
    assert (sent_bundle / f"{images[0].name}").exists()

    # Receiver has it
    r = client.get("/items/cap-single")
    assert r.status_code == 200
    record = r.json()
    assert record["account_id"] == "acc1"
    assert record["items_count"] == 1


def test_duplicate_capture_id_is_deduped(iso_env, client) -> None:
    """V1 trial #5 — pushing the same file twice yields exactly one record."""
    dispatcher = bridge_dispatcher.Dispatcher(
        config=iso_env,
        retry_queue=bridge_retry_queue.RetryQueue(iso_env.retry_queue_file),
        confirm_fn=lambda payload, images: "acc1",
    )

    payload = _make_payload("cap-dup")
    json1, images1 = _write_capture(iso_env.pending_dir, payload)
    dispatcher.handle(json1)

    # Write again with same capture_id
    json2, images2 = _write_capture(iso_env.pending_dir, payload)
    dispatcher.handle(json2)

    r = client.get("/stats")
    assert r.json()["records"] == 1


def test_same_item_different_capture_id_is_deduped_by_hash(iso_env, client) -> None:
    """Same item content hovered twice (different capture_id) → still 1 record.

    The item_hash stored in the payload makes the receiver treat both POSTs
    as the same logical item even though capture_ids differ. The second
    capture is dropped (V1 dedup-by-content extension).
    """
    dispatcher = bridge_dispatcher.Dispatcher(
        config=iso_env,
        retry_queue=bridge_retry_queue.RetryQueue(iso_env.retry_queue_file),
        confirm_fn=lambda payload, images: "acc1",
    )

    shared_hash = "deadbeef" * 8
    payload1 = {**_make_payload("cap-hash-1"), "item_hash": shared_hash}
    payload2 = {**_make_payload("cap-hash-2"), "item_hash": shared_hash}

    json1, _ = _write_capture(iso_env.pending_dir, payload1)
    dispatcher.handle(json1)

    json2, _ = _write_capture(iso_env.pending_dir, payload2)
    dispatcher.handle(json2)

    r = client.get("/stats")
    assert r.json()["records"] == 1, "second capture with same item_hash must be deduped"


def test_receiver_5xx_triggers_retry(iso_env, monkeypatch) -> None:
    """If the receiver returns 5xx, files stay in pending and retry_count climbs."""
    dispatcher = bridge_dispatcher.Dispatcher(
        config=iso_env,
        retry_queue=bridge_retry_queue.RetryQueue(iso_env.retry_queue_file),
        confirm_fn=lambda payload, images: "acc1",
    )

    def _fake_send(receiver_url, payload, image_paths, account_id, timeout_seconds=30.0):
        from bridge.sender import SendResult
        return SendResult(ok=False, deduped=False, retryable=True, status_code=503, error="unavailable")

    monkeypatch.setattr(bridge_dispatcher, "send_payload", _fake_send)

    json_path, _ = _write_capture(iso_env.pending_dir, _make_payload("cap-retry"))
    dispatcher.handle(json_path)

    # File should still be in pending, retry_queue should have it
    assert json_path.exists()
    queue = bridge_retry_queue.RetryQueue(iso_env.retry_queue_file)
    entries = [e for e in queue._entries if e["capture_id"] == "cap-retry"]
    assert len(entries) == 1
    assert entries[0]["retry_count"] == 1


def test_receiver_4xx_moves_to_failed(iso_env, monkeypatch) -> None:
    dispatcher = bridge_dispatcher.Dispatcher(
        config=iso_env,
        retry_queue=bridge_retry_queue.RetryQueue(iso_env.retry_queue_file),
        confirm_fn=lambda payload, images: "acc1",
    )

    def _fake_send(receiver_url, payload, image_paths, account_id, timeout_seconds=30.0):
        from bridge.sender import SendResult
        return SendResult(ok=False, deduped=False, retryable=False, status_code=400, error="bad payload")

    monkeypatch.setattr(bridge_dispatcher, "send_payload", _fake_send)

    json_path, _ = _write_capture(iso_env.pending_dir, _make_payload("cap-bad"))
    dispatcher.handle(json_path)

    assert not json_path.exists()
    failed = iso_env.failed_dir / "cap-bad"
    assert (failed / "payload.json").exists()


def test_stash_kind_skips_confirm_ui(iso_env, client) -> None:
    confirm_calls: list = []
    dispatcher = bridge_dispatcher.Dispatcher(
        config=iso_env,
        retry_queue=bridge_retry_queue.RetryQueue(iso_env.retry_queue_file),
        confirm_fn=lambda payload, images: confirm_calls.append(payload) or "should-not-be-used",
    )

    payload = _make_payload("cap-stash", kind="stash", items=2)
    json_path, _ = _write_capture(iso_env.pending_dir, payload)
    dispatcher.handle(json_path)

    assert confirm_calls == []
    r = client.get("/items/cap-stash")
    assert r.status_code == 200
    assert r.json()["account_id"] == "auto-stash"


def test_polling_watcher_ignores_tmp_files(iso_env, client) -> None:
    seen: list[Path] = []
    watcher = bridge_watcher.PollingWatcher(iso_env, on_new_file=lambda p: seen.append(p))
    watcher._config = iso_env  # ensure reload picked up tmp env

    # Write a .tmp file — must not trigger
    tmp_file = iso_env.pending_dir / ".partial.json.tmp"
    tmp_file.write_text("garbage", encoding="utf-8")
    ready = watcher.scan_once()
    assert ready == []

    # Write a real JSON — first scan sees it, second scan after stability queues it
    payload = _make_payload("cap-watch")
    json_path, _ = _write_capture(iso_env.pending_dir, payload)
    ready = watcher.scan_once()
    assert ready == []
    time.sleep(iso_env.stability_seconds + 0.05)
    ready = watcher.scan_once()
    assert ready == [json_path]


def test_single_capture_without_accounts_falls_back(iso_env, monkeypatch, client) -> None:
    """When accounts.txt is missing and no confirm_fn set, dispatcher falls back."""
    monkeypatch.setattr(bridge_accounts, "DEFAULT_ACCOUNTS_FILE", iso_env.capture_dir / "nope.txt")
    dispatcher = bridge_dispatcher.Dispatcher(
        config=iso_env,
        retry_queue=bridge_retry_queue.RetryQueue(iso_env.retry_queue_file),
    )
    dispatcher.reload_accounts()

    payload = _make_payload("cap-noacc")
    json_path, _ = _write_capture(iso_env.pending_dir, payload)
    dispatcher.handle(json_path)

    r = client.get("/items/cap-noacc")
    assert r.status_code == 200
    assert r.json()["account_id"] == "auto-stash"


def teardown_module(module) -> None:
    # Reset everything we reloaded so other tests don't pick up the temp env.
    importlib.reload(bridge_config)
    importlib.reload(bridge_accounts)
    importlib.reload(bridge_dispatcher)
    importlib.reload(bridge_watcher)
    importlib.reload(bridge_retry_queue)
