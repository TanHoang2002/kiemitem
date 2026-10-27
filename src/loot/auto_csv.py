#!/usr/bin/env python3
"""
Tự động xuất vật phẩm (Items) từ D4LF ra file CSV.
CHỈ XUẤT CÁC VẬT PHẨM ĐƯỢC QUÉT THỰC TẾ TRONG LẦN QUÉT HIỆN TẠI (CURRENT SCAN ONLY).
Tuyệt đối không lấy dữ liệu cũ từ các file log lịch sử trước đó.
"""

import csv
import glob
import logging
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

LOGGER = logging.getLogger(__name__)

CURRENCY_KEYWORDS = [
    "lair key", "greater lair key", "superior lair key",
    "flawless horadric ruby", "flawless horadric skull", "flawless horadric diamond",
    "flawless horadric emerald", "flawless horadric sapphire", "flawless horadric topaz",
    "flawless horadric amethyst", "grand ruby", "grand skull", "grand diamond",
    "grand emerald", "grand sapphire", "grand topaz", "grand amethyst",
    "roots", "crux of the false prophet", "kullean tuning prism",
    "distilled fear", "abyssal splinter"
]

# Bộ nhớ tạm lưu trữ item quét trong lần chạy hiện tại
CURRENT_SCAN_ITEMS = []
CURRENT_SCAN_ACTIVE = False


def is_currency(name: str, item_type: str) -> bool:
    nl = name.lower()
    itl = item_type.lower()
    return any(k in nl for k in CURRENCY_KEYWORDS) or itl in ["lairbosskey", "bosstrophy", "consumable", "gem", "rune"]


class DummyNode(dict):
    """Lớp chứa dữ liệu linh hoạt thay thế dataclass / enum để eval an toàn."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__dict__ = self

    def __getattr__(self, name):
        return self.get(name, None)


def parse_item_line(line: str):
    """Phân tích dòng log chứa 'item based on TTS: Item(...)'."""
    if "Attempt 0 to parse item based on TTS: Item(" not in line:
        return None

    ts_match = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
    timestamp = ts_match.group(1) if ts_match else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    raw_item_str = line.split("item based on TTS: ")[1].strip()

    def _replace_enum(m):
        cls_name = m.group(1)
        member_name = m.group(2)
        val = m.group(3).strip("'\"")
        if cls_name == "AffixType":
            return f"'{member_name}'"
        return f"'{val}'"

    clean_str = re.sub(r"<([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+): ([^>]+)>", _replace_enum, raw_item_str)

    safe_env = {
        "Item": DummyNode,
        "Affix": DummyNode,
        "Aspect": DummyNode,
        "None": None,
        "True": True,
        "False": False,
    }

    try:
        item = eval(clean_str, safe_env)
        return timestamp, item
    except Exception:
        return None


def start_scan():
    """Gọi khi bắt đầu một lượt quét mới (run_loot_filter)."""
    global CURRENT_SCAN_ITEMS, CURRENT_SCAN_ACTIVE
    CURRENT_SCAN_ITEMS.clear()
    CURRENT_SCAN_ACTIVE = True
    LOGGER.info("Bắt đầu phiên quét mới (làm sạch danh sách tạm).")


def record_item(item_descr):
    """Ghi nhận một item vừa được đọc TTS trong phiên quét hiện tại."""
    global CURRENT_SCAN_ITEMS
    now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    CURRENT_SCAN_ITEMS.append((now_ts, item_descr))


def item_to_dict(timestamp: str, item: DummyNode, source_file: str = "current_scan"):
    """Chuyển đổi đối tượng Item thành dictionary hàng CSV kèm số lượng (Quantity)."""
    affixes = item.affixes or []
    ga_count = sum(1 for a in affixes if getattr(a, "type", "") == "greater")

    affix_texts = []
    affix_cols = ["", "", "", "", "", ""]
    for i, a in enumerate(affixes):
        is_ga = " [GA ⭐]" if getattr(a, "type", "") == "greater" else ""
        text = f"{getattr(a, 'text', '')}{is_ga}".strip()
        affix_texts.append(text)
        if i < len(affix_cols):
            affix_cols[i] = text

    aspect_name = ""
    aspect_desc = ""
    aspect_val = ""
    if item.aspect:
        aspect_name = getattr(item.aspect, "name", "") or ""
        aspect_desc = getattr(item.aspect, "text", "") or ""
        val = getattr(item.aspect, "value", None)
        aspect_val = str(val) if val is not None else ""

    # Nếu trang bị có 5 dòng affix và 1 aspect dạng chỉ số (như vũ khí Unique 6 dòng: INSIGHT),
    # dòng aspect chính là Dòng 6 thực tế trên tooltip của vũ khí!
    if len(affixes) == 5 and aspect_desc and not affix_cols[5]:
        is_aspect_ga = ("[" not in aspect_desc) and item.is_ancestral
        aspect_ga_tag = " [GA ⭐]" if is_aspect_ga else ""
        affix_cols[5] = f"{aspect_desc}{aspect_ga_tag}".strip()
        affix_texts.append(affix_cols[5])
        if is_aspect_ga:
            ga_count += 1

    raw_name = item.original_name or item.name or "Unknown Item"
    qty_match = re.search(r"\s*\((\d+)\)\s*$", raw_name)
    if qty_match:
        quantity = int(qty_match.group(1))
        clean_name = re.sub(r"\s*\(\d+\)\s*$", "", raw_name).strip()
    else:
        quantity = 1
        clean_name = raw_name.strip()

    raw_item_type = str(item.item_type or "")
    if is_currency(clean_name, raw_item_type):
        item_type = "Currency"
        rarity = "Currency"
    else:
        item_type = raw_item_type
        rarity = str(item.rarity or "").capitalize()

    power = item.power if item.power is not None else ""
    is_ancestral = "Yes" if item.is_ancestral else "No"
    codex = "Yes" if item.codex_upgrade else "No"
    cosmetic = "Yes" if item.cosmetic_upgrade else "No"

    row = {
        "Thời Gian": timestamp,
        "Tên Trang Bị": clean_name,
        "Số Lượng": quantity,
        "Loại Trang Bị": item_type,
        "Độ Hiếm": rarity,
        "Item Power": power,
        "Tổ Tiên (Ancestral)": is_ancestral,
        "Số Sao (GA ⭐)": ga_count if ga_count > 0 else 0,
        "Dòng 1": affix_cols[0],
        "Dòng 2": affix_cols[1],
        "Dòng 3": affix_cols[2],
        "Dòng 4": affix_cols[3],
        "Dòng 5": affix_cols[4],
        "Dòng 6": affix_cols[5],
        "Tên Aspect": aspect_name,
        "Chỉ Số Aspect Roll": aspect_val,
        "Hiệu Ứng Aspect / Unique": aspect_desc,
        "Codex Mới": codex,
        "Ngoại Trang Mới": cosmetic,
        "Tất Cả Affixes": " | ".join(affix_texts),
        "File Log": source_file,
    }

    return clean_name, item_type, quantity, row


def get_items_from_latest_scan_log():
    """Đọc CHỈ phần quét mới nhất (từ 'Running loot filter' cuối cùng) trong log mới nhất."""
    home = os.path.expanduser("~")
    d4lf_logs_dir = os.path.join(home, "d4lf", "logs")
    if not os.path.isdir(d4lf_logs_dir):
        return []

    log_files = sorted(glob.glob(os.path.join(d4lf_logs_dir, "*.log")), key=os.path.getmtime)
    if not log_files:
        return []

    latest_log = log_files[-1]
    with open(latest_log, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    last_scan_idx = 0
    for idx, l in enumerate(lines):
        if "Running loot filter" in l:
            last_scan_idx = idx

    scan_lines = lines[last_scan_idx:]
    items = []
    for l in scan_lines:
        p = parse_item_line(l)
        if p:
            items.append((p[0], p[1], os.path.basename(latest_log)))
    return items


def finish_scan_and_export():
    """Xuất file CSV chứa DUY NHẤT các item trong lần quét vừa rồi."""
    global CURRENT_SCAN_ITEMS, CURRENT_SCAN_ACTIVE
    home = os.path.expanduser("~")
    output_csv = os.path.join(home, "d4lf", "latest_items.csv")
    currency_csv = os.path.join(home, "d4lf", "currency_inventory.csv")

    items_to_export = []
    if CURRENT_SCAN_ITEMS:
        for ts, it in CURRENT_SCAN_ITEMS:
            items_to_export.append((ts, it, "in_memory"))
    else:
        # Fallback: đọc phiên quét cuối từ log mới nhất
        items_to_export = get_items_from_latest_scan_log()

    CURRENT_SCAN_ITEMS.clear()
    CURRENT_SCAN_ACTIVE = False

    if not items_to_export:
        LOGGER.info("Không có vật phẩm nào được quét trong lượt này.")
        return 0

    # Phân nhóm Currency vs Trang bị thực tế
    currencies_agg = {}  # clean_name -> dict(total, stacks, last_ts, file)
    equipment_rows = []
    seen_gear = set()

    for ts, it, src_file in items_to_export:
        clean_name, item_type, qty, row_data = item_to_dict(ts, it, src_file)
        if item_type == "Currency":
            if clean_name not in currencies_agg:
                currencies_agg[clean_name] = {
                    "total": 0,
                    "stacks": 0,
                    "stack_size": qty,
                    "row": row_data
                }
            currencies_agg[clean_name]["total"] += qty
            currencies_agg[clean_name]["stacks"] += 1
            currencies_agg[clean_name]["row"]["Thời Gian"] = ts
        else:
            # Trang bị thực tế: tránh lặp nếu hover nhiều lần
            gear_key = (
                clean_name,
                row_data["Item Power"],
                row_data["Độ Hiếm"],
                row_data["Tất Cả Affixes"],
                row_data["Tên Aspect"]
            )
            if gear_key not in seen_gear:
                seen_gear.add(gear_key)
                equipment_rows.append(row_data)

    # Tạo các hàng Currency tổng hợp cho lần quét này
    currency_final_rows = []
    for c_name, c_info in currencies_agg.items():
        r = c_info["row"]
        r["Số Lượng"] = c_info["total"]
        if c_info["stacks"] > 1:
            r["Tất Cả Affixes"] = f"{c_info['stacks']} stacks (mỗi stack ~{c_info['stack_size']})"
        currency_final_rows.append(r)

    # Ghép lại danh sách kết quả CHỈ CỦA LƯỢT QUÉT NÀY
    final_rows = currency_final_rows + equipment_rows

    fieldnames = [
        "Thời Gian",
        "Tên Trang Bị",
        "Số Lượng",
        "Loại Trang Bị",
        "Độ Hiếm",
        "Item Power",
        "Tổ Tiên (Ancestral)",
        "Số Sao (GA ⭐)",
        "Dòng 1",
        "Dòng 2",
        "Dòng 3",
        "Dòng 4",
        "Dòng 5",
        "Dòng 6",
        "Tên Aspect",
        "Chỉ Số Aspect Roll",
        "Hiệu Ứng Aspect / Unique",
        "Codex Mới",
        "Ngoại Trang Mới",
        "Tất Cả Affixes",
        "File Log",
    ]

    os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
    temp_csv = output_csv + ".tmp"
    with open(temp_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(final_rows)
    os.replace(temp_csv, output_csv)

    # Xuất file chuyên biệt Currency (chỉ có Currency của lượt quét này)
    cur_summary_rows = []
    for c_name, c_info in sorted(currencies_agg.items()):
        cur_summary_rows.append({
            "Tên Currency": c_name,
            "Tổng Số Lượng": c_info["total"],
            "Số Stack": c_info["stacks"],
            "Chi Tiết": f"{c_info['stacks']} stack(s) x {c_info['stack_size']}",
            "Thời Gian Quét": c_info["row"]["Thời Gian"],
        })

    temp_cur_csv = currency_csv + ".tmp"
    cur_fieldnames = ["Tên Currency", "Tổng Số Lượng", "Số Stack", "Chi Tiết", "Thời Gian Quét"]
    with open(temp_cur_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cur_fieldnames)
        writer.writeheader()
        writer.writerows(cur_summary_rows)
    os.replace(temp_cur_csv, currency_csv)

    LOGGER.info(f"Đã xuất CHÍNH XÁC {len(final_rows)} mặt hàng từ phiên quét thực tế vào {output_csv}")

    # Gửi thông báo Desktop notification trên Linux KDE Wayland
    try:
        logo_path = os.path.join(home, "d4lf", "assets", "logo.png")
        icon_arg = ["-i", logo_path] if os.path.exists(logo_path) else []
        cur_count = len(currencies_agg)
        gear_count = len(equipment_rows)
        subprocess.run(
            ["notify-send", "D4LF Loot Filter", f"Quét thực tế xong!\n{cur_count} loại Currency ({sum(x['total'] for x in currencies_agg.values()):,}) và {gear_count} trang bị", *icon_arg],
            check=False,
            timeout=2,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass

    return len(final_rows)


# Hàm alias để tương thích với các lệnh gọi cũ
auto_export_csv = finish_scan_and_export


if __name__ == "__main__":
    count = finish_scan_and_export()
    print(f"Đã xuất {count} mặt hàng từ lượt quét thực tế ra latest_items.csv và currency_inventory.csv")
