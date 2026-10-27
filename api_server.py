#!/usr/bin/env python3
import csv
import glob
import json
import logging
import os
import subprocess
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
LOGGER = logging.getLogger("d4lf_api_171")

PORT = 18080
ERP_URL = "http://192.168.2.115/api/method/gege_custom.gege_custom.api.inventory.update_bot_inventory"
CURRENCY_CSV = "/home/gege/d4lf/currency_inventory.csv"
ITEMS_CSV = "/home/gege/d4lf/latest_items.csv"
D4LF_LOG = "/home/gege/d4lf_171.log"
DEFAULT_ACCOUNT = "jhondon1#3602"

SLOT_NAMES = {
    "two-handed sword": "2H Sword",
    "two-handed mace": "2H Mace",
    "two-handed axe": "2H Axe",
    "two-handed scythe": "2H Scythe",
    "crossbow": "2H Crossbow",
    "bow": "Bow",
    "staff": "2H Staff",
    "polearm": "2H Polearm",
    "glaive": "2H Glaive",
    "quarterstaff": "2H Quarterstaff",
    "sword": "1H Sword",
    "axe": "1H Axe",
    "mace": "1H Mace",
    "dagger": "Dagger",
    "wand": "Wand",
    "scythe": "1H Scythe",
    "flail": "1H Flail",
    "focus": "Focus",
    "shield": "Shield",
    "totem": "Totem",
    "tome": "Tome",
    "helm": "Helm",
    "chest armor": "Chest",
    "gloves": "Gloves",
    "pants": "Pants",
    "boots": "Boots",
    "amulet": "Amulet",
    "ring": "Ring",
}

def format_item_slot(raw_type: str) -> str:
    cleaned = (raw_type or "").strip().lower()
    if cleaned in SLOT_NAMES:
        return SLOT_NAMES[cleaned]
    if "two-handed" in cleaned:
        return cleaned.replace("two-handed", "2H").title()
    return cleaned.title() if cleaned else ""



def trigger_in_game_scan() -> bool:
    """Tự động focus game Diablo IV và gửi phím 'k' qua ydotool để bot quét rương."""
    LOGGER.info("Bắt đầu tự động kích hoạt quét trong game (gửi phím 'k')...")
    env = os.environ.copy()
    env["YDOTOOL_SOCKET"] = "/run/user/1000/.ydotool_socket"
    env["DISPLAY"] = ":0"
    xauth = glob.glob("/run/user/1000/xauth_*")
    if xauth:
        env["XAUTHORITY"] = xauth[0]

    # 1. Focus cửa sổ game Diablo IV
    try:
        subprocess.run(
            ["xdotool", "search", "--name", "Diablo IV", "windowactivate"],
            env=env,
            timeout=3,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.5)
    except Exception as e:
        LOGGER.warning("Không thể activate cửa sổ Diablo IV qua xdotool: %s", e)

    # 2. Ghi nhận vị trí file log hiện tại
    initial_size = os.path.getsize(D4LF_LOG) if os.path.exists(D4LF_LOG) else 0

    # 3. Gửi phím k (37:1 nhấn, 37:0 nhả) qua ydotool
    res = subprocess.run(
        ["ydotool", "key", "37:1", "37:0"],
        env=env,
        timeout=5,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if res.returncode != 0:
        LOGGER.error("Gửi phím k qua ydotool thất bại (returncode=%d)", res.returncode)
        return False

    LOGGER.info("Đã gửi phím 'k' thành công! Đang chờ bot D4LF hoàn thành quét rương...")

    # 4. Chờ bot hoàn tất quét (tối đa 120 giây để quét hết Equipment + Socketables + Consumables)
    start_time = time.time()
    max_wait = 120
    while time.time() - start_time < max_wait:
        time.sleep(1.0)
        if os.path.exists(D4LF_LOG) and os.path.getsize(D4LF_LOG) > initial_size:
            with open(D4LF_LOG, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(initial_size)
                new_logs = f.read()
                if "Loot filter done" in new_logs:
                    LOGGER.info("Bot D4LF đã hoàn thành toàn bộ quét rương & các tab phụ thành công sau %.1f giây!", time.time() - start_time)
                    time.sleep(1.5)  # Chờ file CSV ghi xong hoàn tất
                    return True

    LOGGER.warning("Hết thời gian chờ (quá %d giây) nhưng chưa thấy 'Loot filter done'. Tiếp tục xuất file...", max_wait)
    return False


def parse_and_send_to_erp(account_id: str, request_id: str | None = None):
    LOGGER.info("Starting scan export and ERP sync for account=%s, request_id=%s", account_id, request_id)

    # 0. Tự động gửi phím k để bot quét thực tế trong game
    try:
        trigger_in_game_scan()
    except Exception as e:
        LOGGER.exception("Lỗi khi tự động kích hoạt phím k: %s", e)

    # 1. Run export_items_csv.py to refresh CSV if possible
    try:
        subprocess.run(
            ["python3", "/home/gege/d4lf/export_items_csv.py", "--all"],
            timeout=30,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        LOGGER.warning("export_items_csv failed or timed out: %s", e)

    currency_items = {}
    try:
        if os.path.exists(CURRENCY_CSV):
            with open(CURRENCY_CSV, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    name = r.get("Tên Currency", "").strip()
                    qty_str = r.get("Tổng Số Lượng", "1").strip()
                    try:
                        qty = int(qty_str)
                    except ValueError:
                        qty = 1
                    if name:
                        cname = f"D4 {name.title()}" if not name.lower().startswith("d4 ") else name
                        currency_items[cname] = currency_items.get(cname, 0) + qty
    except Exception as e:
        LOGGER.exception("Error parsing %s: %s", CURRENCY_CSV, e)

    equipment_items = []
    try:
        if os.path.exists(ITEMS_CSV):
            with open(ITEMS_CSV, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    name = r.get("Tên Trang Bị", "").strip()
                    item_type = r.get("Loại Trang Bị", "").strip()
                    if not name or item_type.lower() in ("currency", "rune"):
                        continue

                    ga_str = r.get("Số Sao (GA ⭐)", "0").strip()
                    power = r.get("Item Power", "").strip()
                    rarity = r.get("Độ Hiếm", "").replace("Itemrarity.", "").strip()
                    affixes = r.get("Tất Cả Affixes", "").strip()
                    aspect = r.get("Tên Aspect", "").strip()
                    aspect_roll = r.get("Chỉ Số Aspect Roll", "").strip()

                    slot_label = format_item_slot(item_type)
                    note_parts = []
                    if ga_str and ga_str != "0":
                        note_parts.append(f"{ga_str} GA ⭐")
                    if slot_label and power:
                        note_parts.append(f"{slot_label} • {power}")
                    elif slot_label:
                        note_parts.append(slot_label)
                    elif power:
                        note_parts.append(f"Power {power}")
                    if rarity:
                        note_parts.append(rarity.title())
                    if affixes:
                        note_parts.append(affixes)
                    if aspect:
                        asp_str = f"Aspect: {aspect}"
                        if aspect_roll:
                            asp_str += f" ({aspect_roll})"
                        note_parts.append(asp_str)

                    note_str = " | ".join(note_parts) if note_parts else "Equipment item"
                    cname = f"D4 {name.title()}" if not name.lower().startswith("d4 ") else name
                    equipment_items.append({
                        "currency_item": cname,
                        "quantity": 1,
                        "note": note_str,
                        "is_item": True
                    })
    except Exception as e:
        LOGGER.exception("Error parsing %s: %s", ITEMS_CSV, e)

    final_items = []
    for cname, qty in currency_items.items():
        final_items.append({
            "currency_item": cname,
            "quantity": qty,
            "note": "",
            "is_item": False
        })
    final_items.extend(equipment_items)

    LOGGER.info("Total items prepared for ERP: %d (currencies: %d, gear: %d)", len(final_items), len(currency_items), len(equipment_items))

    payload = {
        "game_account": account_id,
        "items": final_items
    }
    if request_id:
        payload["request_id"] = request_id

    try:
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            ERP_URL,
            data=req_data,
            headers={"Content-Type": "application/json", "X-API-Key": "giaoit_key_7b9d1e4c8f0a2d5e"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_body = resp.read().decode("utf-8")
            LOGGER.info("ERP Response: %s", resp_body)
    except Exception as e:
        LOGGER.exception("Failed to send inventory to ERP: %s", e)


class ApiHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        LOGGER.debug(format % args)

    def _send_json(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path.rstrip("/")
        query = parse_qs(parsed_url.query)
        account_id = query.get("account_id", [None])[0]

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        target_acc = data.get("game_account") or account_id or DEFAULT_ACCOUNT
        request_id = data.get("request_id")

        if path in ("/scan", "/trigger/f4", "/trigger/f6"):
            LOGGER.info("Received scan trigger for account=%s, request_id=%s", target_acc, request_id)
            threading.Thread(
                target=parse_and_send_to_erp,
                args=(target_acc, request_id),
                daemon=True
            ).start()
            self._send_json(200, {
                "ok": True,
                "action": "scan_started",
                "game_account": target_acc,
                "request_id": request_id
            })
        elif path == "/health":
            self._send_json(200, {"ok": True, "status": "online", "account": DEFAULT_ACCOUNT})
        else:
            self._send_json(404, {"ok": False, "error": "Not Found"})

    def do_GET(self):
        if self.path in ("/health", "/health/"):
            self._send_json(200, {"ok": True, "status": "online", "account": DEFAULT_ACCOUNT})
        else:
            self.do_POST()


def main():
    server = HTTPServer(("0.0.0.0", PORT), ApiHandler)
    LOGGER.info("D4LF Linux API server listening on http://0.0.0.0:%d", PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
