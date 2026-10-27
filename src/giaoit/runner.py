"""Top-level runners invoked by hotkey handlers in src.app.handler.

Each runner is a no-arg callable suitable for handing to
``ScriptHandler._start_or_stop_loot_interaction_thread``. They check the
master switch first so a stray keypress with capture_mode off is a no-op.
"""

import logging

from src.giaoit.capture import capture_item_at_cursor
from src.giaoit.config import is_capture_enabled
from src.giaoit.stash_scan import read_full_stash
from src.giaoit.writer import write_capture

LOGGER = logging.getLogger(__name__)


def run_capture_single() -> None:
    """F2: capture the item under the cursor."""
    if not is_capture_enabled():
        LOGGER.info("GiaoIT capture_single pressed but capture_mode is disabled; ignoring")
        return

    bundle = capture_item_at_cursor()
    if bundle is None:
        LOGGER.warning("GiaoIT capture_single produced no bundle")
        return

    write_capture(bundle)


def run_capture_stash(account_id: str | None = None, request_id: str | None = None) -> None:
    """F4: read every item in the open stash tabs."""
    if not is_capture_enabled():
        LOGGER.info("GiaoIT capture_stash pressed but capture_mode is disabled; ignoring")
        return

    bundle = read_full_stash()
    if bundle is None:
        LOGGER.warning("GiaoIT capture_stash produced no bundle")
        return

    write_capture(bundle, account_id=account_id, request_id=request_id)


def run_capture_currency(account_id: str | None = None) -> None:
    """F6: read every item in stash, write bundle, and print/log currency counts."""
    if not is_capture_enabled():
        LOGGER.info("GiaoIT capture_currency pressed but capture_mode is disabled; ignoring")
        return

    bundle = read_full_stash()
    if bundle is None:
        LOGGER.warning("GiaoIT capture_currency produced no bundle")
        return

    # For currency scans, we compute the counts FIRST and replace the bundle items
    # with synthetic items representing all known currency types (including 0s).
    # This forces the Web Server to overwrite old quantities with 0 if an item is missing.
    try:
        import re
        from collections import Counter
        from src.item.models import Item
        from src.giaoit.models import CapturedItem

        counts = Counter()
        for captured in bundle.items:
            item = captured.item
            orig_name = str(item.original_name or "").lower()
            name = str(item.name or "").lower()
            quantity = getattr(item, "quantity", 1)

            # 1. Greater Lair Key
            if "greater lair" in orig_name or "greater lair" in name:
                counts["Greater Lair Key"] += quantity
            # 2. Superior Lair Key (must be before Lair Key)
            elif "superior" in orig_name or "superior" in name:
                counts["Superior Lair Key"] += quantity
            # 3. Lair Key
            elif "lair" in orig_name or "lair" in name:
                if (
                    "greater" not in orig_name
                    and "greater" not in name
                    and "superior" not in orig_name
                    and "superior" not in name
                ):
                    counts["Lair Key"] += quantity
            # 4. Corrupted Roots
            elif "root" in orig_name or "root" in name:
                counts["Corrupted Roots"] += quantity
            # 5. Crux of the False Prophet
            elif "crux" in orig_name or "crux" in name:
                counts["Crux of the False Prophet"] += quantity
            # 6. Grand Gems (7 types)
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
            # 7. Flawless Gems (7 types)
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

        LOGGER.info("=" * 50)
        LOGGER.info("📊 THỐNG KÊ SỐ LƯỢNG CURRENCY (F6):")
        LOGGER.info("=" * 50)

        from src.game_data import ItemType, ItemRarity
        # Added keys as requested by the user
        supported_keys = [
            "Corrupted Roots",
            "Lair Key", "Greater Lair Key", "Superior Lair Key",
            "Crux of the False Prophet",
            "Grand Skull", "Grand Ruby", "Grand Sapphire", "Grand Topaz", "Grand Emerald", "Grand Diamond", "Grand Amethyst",
            "Flawless Skull", "Flawless Ruby", "Flawless Sapphire", "Flawless Topaz", "Flawless Emerald", "Flawless Diamond", "Flawless Amethyst"
        ]

        synthetic_items = []
        for key in supported_keys:
            count = counts.get(key, 0)
            LOGGER.info(f"🔹 {key:40}: {count:5d}")
            
            # The server seems to expect the raw TTS string which is often uppercase
            # And it expects "D4 Flawless Horadric Diamond" format for Flawless gems
            send_name = key
            if "Flawless" in key:
                send_name = key.replace("Flawless", "D4 Flawless Horadric")
            
            orig_name = f"{send_name} ({count})".upper()
            
            synth_item = Item(
                name=None, 
                original_name=orig_name,
                item_type=ItemType.Consumable,
                rarity=ItemRarity.Rare
            )
            # Add dynamic quantity so getattr(item, 'quantity', 1) still works if needed downstream
            synth_item.quantity = count
            synthetic_items.append(CapturedItem(item=synth_item, image=None, image_file=None))

        LOGGER.info("-" * 50)
        LOGGER.info(f"Tổng số nguyên liệu gửi lên Server (Gems & Roots): {len(synthetic_items)}")
        LOGGER.info("=" * 50)

        # Replace the bundle's raw items with our clean, counted list
        bundle.items = synthetic_items

    except Exception:
        LOGGER.exception("Failed to compute currency statistics")

    bundle.kind = "currency"
    json_path = write_capture(bundle, account_id=account_id, request_id=request_id)
    if json_path is None:
        return

