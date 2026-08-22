import json
import pathlib
import re
from collections import Counter


def get_latest_stash_payload():
    giaoit_dir = pathlib.Path.home() / ".giaoit"

    # 1. Check pending directory
    pending_file = giaoit_dir / "captures" / "pending" / "latest_stash.json"
    if pending_file.exists():
        return pending_file

    # 2. Check sent directory for latest stash folder
    sent_dir = giaoit_dir / "captures" / "sent"
    if sent_dir.exists():
        stash_folders = list(sent_dir.glob("latest_stash*"))
        if stash_folders:
            stash_folders.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            payload_file = stash_folders[0] / "payload.json"
            if payload_file.exists():
                return payload_file

    # 3. Check received directory for latest JSON
    received_dir = giaoit_dir / "received"
    if received_dir.exists():
        received_files = list(received_dir.glob("*.json"))
        if received_files:
            received_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            for f in received_files:
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    if data.get("kind") == "stash" or data.get("payload", {}).get("kind") == "stash":
                        return f
                except Exception:
                    continue

    return None


def main():
    payload_path = get_latest_stash_payload()
    if not payload_path:
        print("\n❌ Không tìm thấy tệp dữ liệu rương đã quét nào.")
        print("Vui lòng mở rương đồ trong game và bấm F6 để quét rương trước.")
        return

    print(f"\n📂 Đang đọc dữ liệu từ tệp: {payload_path.name}")
    try:
        data = json.loads(payload_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ Lỗi đọc tệp JSON: {e}")
        return

    payload_data = data.get("payload", data)
    items_list = payload_data.get("items", [])

    if not items_list:
        print("ℹ️ Rương đã quét không chứa vật phẩm nào.")
        return

    counts = Counter()
    total_slots = len(items_list)

    for item_entry in items_list:
        item = item_entry.get("item", {})
        orig_name = str(item.get("original_name", "")).lower()
        name = str(item.get("name", "")).lower()

        # Extract stack size from parentheses: e.g. "GREATER LAIR KEY (1000)" -> 1000
        match = re.search(r"\((\d+)\)", orig_name)
        quantity = int(match.group(1)) if match else 1

        # Match categories
        # 1. Greater Lair Key
        if "greater lair" in orig_name or "greater lair" in name:
            counts["Greater Lair Key"] += quantity
        # 2. Lair Key
        elif "lair" in orig_name or "lair" in name:
            if (
                "greater" not in orig_name
                and "greater" not in name
                and "superior" not in orig_name
                and "superior" not in name
            ):
                counts["Lair Key"] += quantity
        # 3. Superior Lair Key
        elif "superior" in orig_name or "superior" in name:
            counts["Superior Lair Key"] += quantity
        # 4. Corrupted Roots
        elif "root" in orig_name or "root" in name:
            counts["Corrupted Roots"] += quantity
        # 5. Crux of the False Prophet
        elif "crux" in orig_name or "crux" in name:
            counts["Crux of the False Prophet"] += quantity
        # 6. Grand Gems
        elif "grand" in orig_name or "grand" in name:
            if "skull" in orig_name or "skull" in name:
                counts["Grand Skull"] += quantity
            elif "ruby" in orig_name or "ruby" in name:
                counts["Grand Ruby"] += quantity
            elif "sapphire" in orig_name or "sapphire" in name:
                counts["Grand Sapphire"] += quantity
            elif "topaz" in orig_name or "topaz" in name:
                counts["Grand Topaz"] += quantity
            elif "emerald" in orig_name or "emerald" in name:
                counts["Grand Emerald"] += quantity
            elif "diamond" in orig_name or "diamond" in name:
                counts["Grand Diamond"] += quantity
            elif "amethyst" in orig_name or "amethyst" in name:
                counts["Grand Amethyst"] += quantity
        # 7. Flawless Gems
        elif ("flawless" in orig_name and "horadric" in orig_name) or ("flawless" in name and "horadric" in name):
            if "skull" in orig_name or "skull" in name:
                counts["Flawless Skull"] += quantity
            elif "ruby" in orig_name or "ruby" in name:
                counts["Flawless Ruby"] += quantity
            elif "sapphire" in orig_name or "sapphire" in name:
                counts["Flawless Sapphire"] += quantity
            elif "topaz" in orig_name or "topaz" in name:
                counts["Flawless Topaz"] += quantity
            elif "emerald" in orig_name or "emerald" in name:
                counts["Flawless Emerald"] += quantity
            elif "diamond" in orig_name or "diamond" in name:
                counts["Flawless Diamond"] += quantity
            elif "amethyst" in orig_name or "amethyst" in name:
                counts["Flawless Amethyst"] += quantity

    print("\n==============================================")
    print("📊 KẾT QUẢ THỐNG KÊ SỐ LƯỢNG CURRENCY (F6):")
    print("==============================================")

    display_keys = [
        "Greater Lair Key",
        "Lair Key",
        "Superior Lair Key",
        "Corrupted Roots",
        "Crux of the False Prophet",
        "Grand Skull",
        "Grand Ruby",
        "Grand Sapphire",
        "Grand Topaz",
        "Grand Emerald",
        "Grand Diamond",
        "Grand Amethyst",
        "Flawless Skull",
        "Flawless Ruby",
        "Flawless Sapphire",
        "Flawless Topaz",
        "Flawless Emerald",
        "Flawless Diamond",
        "Flawless Amethyst",
    ]

    for key in display_keys:
        count = counts.get(key, 0)
        print(f"🔹 {key:30} : {count:5d}")

    print("----------------------------------------------")
    print(f"Tổng số ô vật phẩm đã quét trong rương: {total_slots}")
    print("==============================================\n")


if __name__ == "__main__":
    main()
