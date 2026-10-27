"""HTTP client that posts a captured payload to the receiver."""

import json
import re
from pathlib import Path
from typing import Any

import httpx

from bridge.log import get_logger

LOGGER = get_logger()

CURRENCY_NAMES = {
    "lair key": "D4 Lair Key",
    "greater lair key": "D4 Greater Lair Key",
    "superior lair key": "D4 Superior Lair Key",
    "corrupted roots": "D4 Corrupted Roots",
    "roots": "D4 Corrupted Roots",
    "crux of the false prophet": "D4 Crux",
    "crux": "D4 Crux",
    "kullean tuning prism": "D4 Kullean Tuning Prism",
    "distilled fear": "D4 Distilled Fear",
    "abyssal splinter": "D4 Abyssal Splinter",
    "flawless horadric ruby": "D4 Flawless Horadric Ruby",
    "flawless horadric skull": "D4 Flawless Horadric Skull",
    "flawless horadric diamond": "D4 Flawless Horadric Diamond",
    "flawless horadric emerald": "D4 Flawless Horadric Emerald",
    "flawless horadric sapphire": "D4 Flawless Horadric Sapphire",
    "flawless horadric topaz": "D4 Flawless Horadric Topaz",
    "flawless horadric amethyst": "D4 Flawless Horadric Amethyst",
    "grand ruby": "D4 Grand Ruby",
    "grand skull": "D4 Grand Skull",
    "grand diamond": "D4 Grand Diamond",
    "grand emerald": "D4 Grand Emerald",
    "grand sapphire": "D4 Grand Sapphire",
    "grand topaz": "D4 Grand Topaz",
    "grand amethyst": "D4 Grand Amethyst",
}


def extract_erp_items(items_list: list) -> list[dict[str, Any]]:
    """Convert raw captured items list to ERP items format (aggregated currency + detailed gear)."""
    currency_totals: dict[str, int] = {}
    equipment_items: list[dict[str, Any]] = []

    for it in items_list:
        item_data = it.get("item", {}) if isinstance(it, dict) else getattr(it, "item", it)
        orig_name = str(getattr(item_data, "original_name", "") or (item_data.get("original_name") if isinstance(item_data, dict) else "")).strip()
        if not orig_name:
            continue

        orig_lower = orig_name.lower()

        # Check currency
        is_curr = False
        curr_matched_name = None
        for k, v in CURRENCY_NAMES.items():
            if k in orig_lower:
                is_curr = True
                curr_matched_name = v
                break

        match_qty = re.search(r"\((\d+)\)$", orig_name)
        qty = int(match_qty.group(1)) if match_qty else 1

        if is_curr or match_qty or any(c in orig_lower for c in ["key", "gem", "ruby", "skull", "diamond", "emerald", "sapphire", "topaz", "amethyst"]):
            clean_name = re.sub(r"\s*\(\d+\)$", "", orig_name).strip()
            if not curr_matched_name:
                curr_matched_name = f"D4 {clean_name.title()}"
            currency_totals[curr_matched_name] = currency_totals.get(curr_matched_name, 0) + qty
        else:
            # Equipment item
            affixes = getattr(item_data, "affixes", []) or (item_data.get("affixes") if isinstance(item_data, dict) else [])
            ga_count = sum(1 for a in affixes if (getattr(a, "type", "") == "greater" or (isinstance(a, dict) and a.get("type") in ("greater", "GREATER"))))

            affix_texts = []
            for a in affixes:
                a_text = getattr(a, "text", "") or (a.get("text") if isinstance(a, dict) else "")
                a_type = getattr(a, "type", "") or (a.get("type") if isinstance(a, dict) else "")
                is_ga = " [GA ⭐]" if str(a_type).lower() == "greater" else ""
                if a_text:
                    affix_texts.append(f"{a_text}{is_ga}")

            power = getattr(item_data, "power", "") or (item_data.get("power") if isinstance(item_data, dict) else "")
            rarity = getattr(item_data, "rarity", "") or (item_data.get("rarity") if isinstance(item_data, dict) else "")
            if hasattr(rarity, "value"):
                rarity = rarity.value

            aspect = getattr(item_data, "aspect", None) or (item_data.get("aspect") if isinstance(item_data, dict) else None)
            aspect_name = ""
            if aspect:
                aspect_name = getattr(aspect, "name", "") or (aspect.get("name") if isinstance(aspect, dict) else "")

            stats_parts = []
            if ga_count > 0:
                stats_parts.append(f"{ga_count} GA ⭐")
            if power:
                stats_parts.append(f"Power {power}")
            if rarity:
                stats_parts.append(str(rarity).title())
            if affix_texts:
                stats_parts.append(" | ".join(affix_texts))
            if aspect_name:
                stats_parts.append(f"Aspect: {aspect_name}")

            note_str = " | ".join(stats_parts) if stats_parts else "Equipment item"

            item_name = orig_name.title()
            if not item_name.startswith("D4 "):
                item_name = f"D4 {item_name}"

            equipment_items.append({
                "currency_item": item_name,
                "quantity": 1,
                "note": note_str,
                "is_item": True,
            })

    mapped: list[dict[str, Any]] = []
    for ci_name, total_q in currency_totals.items():
        mapped.append({
            "currency_item": ci_name,
            "quantity": total_q,
            "note": "",
            "is_item": False,
        })
    mapped.extend(equipment_items)
    return mapped


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
    receiver_url: str,
    payload: dict[str, Any],
    image_paths: list[Path],
    account_id: str,
    timeout_seconds: float = 30.0,
    api_key: str = None,
) -> SendResult:
    files: list[tuple[str, tuple[str, bytes, str]]] = []
    for path in image_paths:
        try:
            files.append(("images", (path.name, path.read_bytes(), "image/png")))
        except OSError:
            LOGGER.warning("failed to read image %s; skipping", path)

    items_list = payload.get("items", [])
    mapped_items = extract_erp_items(items_list)

    final_acc = account_id or payload.get("account_id") or "hisaeapar#3677 / Kled"
    payload_to_erp = {
        "game_account": final_acc,
        "items": mapped_items,
    }

    request_id = payload.get("request_id")
    if request_id:
        payload_to_erp["request_id"] = request_id

    url = receiver_url
    if not (url.endswith("/items") or "/api/method" in url):
        url = f"{url}/items"

    headers = {}
    if api_key:
        if ":" in api_key:
            token_val = api_key if api_key.startswith("token ") else f"token {api_key}"
            headers["Authorization"] = token_val
        else:
            headers["X-API-Key"] = api_key

    try:
        response = httpx.post(url, json=payload_to_erp, headers=headers, timeout=timeout_seconds)
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
