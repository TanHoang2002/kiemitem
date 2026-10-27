"""GiaoIT V1 receiver stub — FastAPI app.

Endpoints:
  POST /items              multipart: payload=JSON string, account_id=string, images=PNG files
  GET  /items/{capture_id}
  GET  /health
  GET  /stats
"""

import json
import time
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse

from receiver.storage import Storage, get_store

SCHEMA = "giaoit.capture.v1"
START_TIME = time.monotonic()


import os

GIAOIT_API_KEY = os.environ.get("GIAOIT_API_KEY", "giaoit_key_7b9d1e4c8f0a2d5e")


def verify_api_key(x_api_key: str = Header(None), api_key: str = Query(None)):
    key = x_api_key or api_key
    if not key or key != GIAOIT_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid or missing API key")


app = FastAPI(title="GiaoIT V1 Receiver Stub", version="0.1.0")

PENDING_SCANS = {}


@app.post("/scan", dependencies=[Depends(verify_api_key)])
async def receive_scan_trigger(data: dict = None) -> dict[str, object]:
    """Called by ERP to trigger bot scan on client machine."""
    if not data:
        return {"status": "error", "message": "Missing payload"}
    game_account = data.get("game_account")
    request_id = data.get("request_id")
    if game_account:
        PENDING_SCANS[game_account] = request_id
        import httpx

        async with httpx.AsyncClient() as client:
            try:
                # Trigger scan locally on the client bot (F6 for currency/inventory scan)
                await client.post(f"http://localhost:18080/trigger/f6?account_id={game_account}", timeout=5)
            except Exception:
                pass
    return {"status": "ok"}


def _storage() -> Storage:
    return get_store()


@app.get("/health")
def health() -> dict[str, object]:
    return {"ok": True, "uptime_s": round(time.monotonic() - START_TIME, 3)}


@app.get("/stats")
def stats() -> dict[str, object]:
    return {"records": _storage().count()}


@app.post("/items", dependencies=[Depends(verify_api_key)])
async def post_items(
    payload: Annotated[str, Form()],
    account_id: Annotated[str, Form()],
    images: Annotated[list[UploadFile], File()] = [],
) -> JSONResponse:
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"invalid payload JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="payload must be a JSON object")

    if parsed.get("schema") != SCHEMA:
        raise HTTPException(status_code=400, detail=f"unsupported schema: {parsed.get('schema')!r}")

    capture_id = parsed.get("capture_id")
    if not isinstance(capture_id, str) or not capture_id:
        raise HTTPException(status_code=400, detail="missing capture_id")

    # Persist uploaded images to ~/.giaoit/received/<capture_id>/<filename>
    record, deduped_by_id, deduped_by_hash = _storage().put(capture_id, parsed, account_id)
    if not deduped_by_id and not deduped_by_hash:
        _persist_images(capture_id, images)

    deduped = deduped_by_id or deduped_by_hash
    status_code = 200 if deduped else 201

    # Forward/post to ERP after database persistence
    request_id = PENDING_SCANS.pop(account_id, None)

    from receiver.storage import _extract_currencies

    counts = _extract_currencies(parsed)
    mapped_items = [{"currency_item": ci, "quantity": qty} for ci, qty in counts.items()]

    import httpx

    # Forward payload to the ERP server
    erp_url = "http://192.168.2.115/api/method/gege_custom.gege_custom.api.inventory.update_bot_inventory"
    headers = {"X-API-Key": GIAOIT_API_KEY, "Content-Type": "application/json"}
    payload_to_erp = {"game_account": account_id, "items": mapped_items}
    if request_id:
        payload_to_erp["request_id"] = request_id

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(erp_url, json=payload_to_erp, headers=headers, timeout=10)
            print(f"ERP API Response: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"ERP API Error: {e}")

    return JSONResponse(
        status_code=status_code,
        content={
            "ok": True,
            "id": record["capture_id"],
            "capture_id": record["capture_id"],
            "deduped": deduped,
            "deduped_by_capture_id": deduped_by_id,
            "deduped_by_hash": deduped_by_hash,
            "items_count": record["items_count"],
        },
    )


@app.get("/items/{capture_id}")
def get_item(capture_id: str) -> JSONResponse:
    record = _storage().get(capture_id)
    if record is None:
        raise HTTPException(status_code=404, detail="not found")
    return JSONResponse(status_code=200, content=record)


@app.get("/warehouse")
def get_warehouse_summary() -> dict[str, Any]:
    """Get the latest currency warehouse state grouped by account_id."""
    import re
    from collections import Counter
    from datetime import datetime

    storage = _storage()
    # Group records by account_id, keeping the latest one by received_at
    latest_records = {}
    with storage._lock:
        for record in storage._records.values():
            if record.get("kind") not in ("stash", "currency"):
                continue
            acc_id = record.get("account_id")
            if not acc_id:
                continue
            received_at = record.get("received_at", "")

            if acc_id not in latest_records or received_at > latest_records[acc_id].get("received_at", ""):
                latest_records[acc_id] = record

    summary = {}
    for acc_id, record in latest_records.items():
        payload_data = record.get("payload", {})
        items_list = payload_data.get("items", [])
        counts = Counter()

        for item_entry in items_list:
            item = item_entry.get("item", {})
            orig_name = str(item.get("original_name", "")).lower()
            name = str(item.get("name", "")).lower()

            # Extract stack size
            match = re.search(r"\((\d+)\)", orig_name)
            quantity = int(match.group(1)) if match else 1

            # Match categories
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
                gem_type = next(
                    (
                        g
                        for g in ["skull", "ruby", "sapphire", "topaz", "emerald", "diamond", "amethyst"]
                        if g in orig_name
                    ),
                    "other",
                )
                counts[f"Grand {gem_type.capitalize()}"] += quantity
            elif ("flawless" in orig_name and "horadric" in orig_name) or ("flawless" in name and "horadric" in name):
                gem_type = next(
                    (
                        g
                        for g in ["skull", "ruby", "sapphire", "topaz", "emerald", "diamond", "amethyst"]
                        if g in orig_name
                    ),
                    "other",
                )
                counts[f"Flawless {gem_type.capitalize()}"] += quantity

        # Format the time
        received_at_str = record.get("received_at", "")
        try:
            # simple ISO parsing
            dt_str = received_at_str.replace("Z", "+00:00")
            # handle milliseconds if present
            if "." in dt_str:
                dt = datetime.strptime(dt_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")
            else:
                dt = datetime.fromisoformat(dt_str)
            last_updated = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except Exception:
            last_updated = received_at_str

        summary[acc_id] = {"last_updated": last_updated, "currencies": dict(counts)}

    return summary


@app.get("/warehouse/history", dependencies=[Depends(verify_api_key)])
def get_warehouse_history() -> list[dict[str, Any]]:
    """Get the transaction history list of warehouse updates."""
    return _storage().get_history()


def _persist_images(capture_id: str, images: list[UploadFile]) -> None:
    if not images:
        return
    target_dir = Path.home() / ".giaoit" / "received" / capture_id
    target_dir.mkdir(parents=True, exist_ok=True)
    for image in images:
        filename = Path(image.filename or "image.png").name
        if not filename.endswith(".png"):
            continue
        target = target_dir / filename
        try:
            target.write_bytes(image.file.read())
        except OSError:
            pass
