import logging
import time

from src.automation.inventory import InventoryBase
from src.automation.mouse import Mouse
from src.perception import SearchArgs, window_to_monitor
from src.settings import get_settings, get_ui_coordinates

LOGGER = logging.getLogger(__name__)

CHAR_TAB_NAMES = {
    0: "Equipment",
    1: "Aspects",
    2: "Socketables",
    3: "Consumables",
    4: "QuestItems",
}


class CharInventory(InventoryBase):
    def __init__(self) -> None:
        super().__init__()
        self.menu_name = "Char_Inventory"
        sort_icon_roi = [int(value) for value in get_ui_coordinates().roi.sort_icon]
        self.is_open_search_args = SearchArgs(
            ref=["sort_icon", "sort_icon_hover"], threshold=0.8, roi=sort_icon_roi, use_grayscale=False
        )
        self.open_hotkey = get_settings().char.inventory
        self.delay = 1  # Needed as they added a "fade-in" for the items
        self.curr_tab = 0

    def switch_to_tab(self, tab_idx: int) -> bool:
        tab_name = CHAR_TAB_NAMES.get(tab_idx, str(tab_idx))
        LOGGER.info(f"Switch Character Inventory Tab to: {tab_idx} ({tab_name})")
        if tab_idx < 0 or tab_idx > 4:
            return False
        if getattr(self, "curr_tab", 0) == tab_idx:
            return True
        try:
            x, y, w, h = get_ui_coordinates().roi.char_tab_slots
        except Exception:
            slots_roi = get_ui_coordinates().roi.slots_3x11
            sort_roi = get_ui_coordinates().roi.sort_icon
            w = int(slots_roi[2] * (440.0 / 1214.0))
            x = int(slots_roi[0] + slots_roi[2] - w)
            y = int(sort_roi[1] - (sort_roi[3] * 0.1))
            h = int(sort_roi[3] * 0.6)

        section_length = w // 5
        center = (x + int((tab_idx + 0.5) * section_length), y + h // 2)
        Mouse.move(*window_to_monitor(center), randomize=3)
        time.sleep(0.12)
        Mouse.click("left")
        self.curr_tab = tab_idx
        time.sleep(0.35)
        return True
