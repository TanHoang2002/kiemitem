"""Loot interaction orchestration shared by the application handler."""

import logging
import os
import time

import cv2

from src.automation import character_inventory, move_pointer, stash_inventory
from src.automation.mouse import Mouse
from src.loot.filter import check_items
from src.perception import abs_window_to_monitor, capture, screenshot, window_to_monitor
from src.settings import ItemRefreshType, get_settings

LOGGER = logging.getLogger(__name__)


def auto_open_chest() -> bool:
    """Detects the stash chest on screen and clicks to open it."""
    LOGGER.info("Stash is not open. Detecting chest location to auto-open...")
    img = capture(force_new=True)
    if img is None:
        LOGGER.warning("Could not capture screen for chest detection")
        return False

    chest_coords = None
    best_score = 0.0

    from src.settings import BASE_DIR

    # Giới hạn vùng tìm kiếm trong thế giới game xung quanh nhân vật
    # Loại trừ thanh kỹ năng / bình máu / UI ở đáy màn hình (y >= 680) và thanh menu ở đỉnh (y < 100)
    h_img, w_img = img.shape[:2]
    roi_top = 100
    roi_bottom = min(h_img, 680)
    roi_left = 300
    roi_right = min(w_img, 1600)
    cropped_game_world = img[roi_top:roi_bottom, roi_left:roi_right]

    # Search using template matching
    for tmpl_name in ["chest_template.png", "chest_template_alt.png"]:
        tmpl_path = str(BASE_DIR / "assets" / "templates" / tmpl_name)
        tmpl = cv2.imread(tmpl_path)
        if tmpl is None:
            continue
        res = cv2.matchTemplate(cropped_game_world, tmpl, cv2.TM_CCOEFF_NORMED)
        min_v, max_v, min_l, max_l = cv2.minMaxLoc(res)
        LOGGER.debug(f"Chest template {tmpl_name}: score={max_v:.3f} at relative {max_l}")
        if max_v >= 0.45 and max_v > best_score:
            h, w = tmpl.shape[:2]
            # Chuyển đổi lại toạ độ toàn màn hình
            chest_coords = (roi_left + max_l[0] + w // 2, roi_top + max_l[1] + h // 2)
            best_score = max_v

    if chest_coords is not None:
        LOGGER.info(f"Visually detected chest at {chest_coords} (confidence: {best_score:.3f})")
    else:
        # Fallback coordinate when player stands in Kyovashad / standard chest corner
        chest_coords = (850, 480)
        LOGGER.info(f"Chest template not matched (best: {best_score:.3f}); using fallback {chest_coords}")

    # Move mouse and click to interact with the chest
    mx, my = window_to_monitor(chest_coords)
    LOGGER.info(f"Clicking chest at monitor coordinates ({mx}, {my})...")
    Mouse.move(mx, my, randomize=8)
    time.sleep(0.12)
    Mouse.click("left")

    # Wait for the Stash UI to open
    stash = stash_inventory()
    start_wait = time.time()
    while time.time() - start_wait < 3.0:
        time.sleep(0.4)
        if stash.is_open(capture(force_new=True)):
            LOGGER.info("Stash UI opened successfully!")
            return True

    LOGGER.warning("Stash UI did not open after clicking chest")
    return False


def _get_char_tabs_to_check() -> list[int]:
    """Lấy danh sách các tab phụ trong túi đồ cần quét (2: Socketables, 3: Consumables)."""
    try:
        import configparser
        from pathlib import Path
        cp = configparser.ConfigParser()
        ini_path = Path.home() / ".d4lf" / "params.ini"
        if ini_path.exists():
            cp.read(ini_path)
            if cp.has_option("general", "check_char_tabs"):
                val = cp.get("general", "check_char_tabs").strip()
                if val.lower() in ("none", "false", "0", ""):
                    return []
                return [int(x.strip()) for x in val.split(",") if x.strip().isdigit()]
    except Exception:
        pass
    return [2, 3]  # Mặc định quét thêm Tab 2 (Socketables) và Tab 3 (Consumables)


def run_loot_filter(force_refresh: ItemRefreshType = ItemRefreshType.no_refresh, no_match_action: str = "junk") -> None:
    LOGGER.info("Running loot filter")
    try:
        from src.loot.auto_csv import start_scan
        start_scan()
    except Exception:
        pass
    move_pointer(*abs_window_to_monitor((0, 0)))
    inv = character_inventory()
    stash = stash_inventory()

    # 1. If stash is closed, attempt to auto-detect and open the chest
    if not stash.is_open(capture(force_new=True)):
        auto_open_chest()

    # 2. If stash is open, scan configured chest tabs and character inventory
    if stash.is_open():
        for tab in get_settings().general.check_chest_tabs:
            stash.switch_to_tab(tab)
            time.sleep(0.4)
            check_items(stash, force_refresh, stash_is_open=True, no_match_action="junk")
        move_pointer(*abs_window_to_monitor((0, 0)))
        time.sleep(0.3)
        check_items(inv, force_refresh, stash_is_open=True, no_match_action="junk")
        # Quét thêm các tab Socketables và Consumables trong túi đồ khi mở rương
        extra_char_tabs = _get_char_tabs_to_check()
        for char_tab in extra_char_tabs:
            if hasattr(inv, "switch_to_tab"):
                inv.switch_to_tab(char_tab)
                time.sleep(0.4)
                check_items(inv, force_refresh, stash_is_open=True, no_match_action="junk")
        if hasattr(inv, "switch_to_tab") and extra_char_tabs:
            inv.switch_to_tab(0)
            time.sleep(0.2)
    else:
        # If not standing near chest or chest failed to open, open character inventory
        if not inv.open():
            screenshot("inventory_not_open", img=capture())
            LOGGER.error("Inventory did not open up")
            return
        # 1. Quét tab vũ khí / trang bị mặc định (Tab 0: Equipment)
        check_items(inv, force_refresh, no_match_action=no_match_action)

        # 2. Sau khi quét xong vũ khí, chuột tự lia theo quỹ đạo cong để quét thêm mục Socketables (tab 2) và Consumables (tab 3)
        extra_char_tabs = _get_char_tabs_to_check()
        for char_tab in extra_char_tabs:
            LOGGER.info(f"Scanning additional character inventory tab: {char_tab}")
            if hasattr(inv, "switch_to_tab"):
                inv.switch_to_tab(char_tab)
                time.sleep(0.4)
                check_items(inv, force_refresh, no_match_action=no_match_action)

        # 3. Trả về lại tab Equipment (tab 0) để sẵn sàng cho lần mở túi đồ tiếp theo
        if hasattr(inv, "switch_to_tab") and extra_char_tabs:
            inv.switch_to_tab(0)
            time.sleep(0.2)

    move_pointer(*abs_window_to_monitor((0, 0)))
    LOGGER.info("Loot filter done")
    try:
        from src.loot.auto_csv import finish_scan_and_export
        finish_scan_and_export()
    except Exception as e:
        LOGGER.error(f"Lỗi khi tự động xuất CSV: {e}")


