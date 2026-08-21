import logging
import typing
from types import SimpleNamespace

if typing.TYPE_CHECKING:
    from pytest_mock import MockerFixture

from src.game_data import ItemRarity, ItemType
from src.item import Affix, AffixType, FilterResult, Item
from src.loot import filter as _filter
from src.loot.filter import check_items
from src.settings import ItemRefreshType


def test_force_without_filter_only_refreshes_item_status(monkeypatch, mocker: MockerFixture):
    inventory = mocker.Mock()
    inventory.get_item_slots.return_value = ([], [])
    reset = mocker.Mock()
    monkeypatch.setattr(_filter, "reset_item_status", reset)

    check_items(inventory, ItemRefreshType.force_without_filter)

    reset.assert_called_once_with([], inventory)
    inventory.hover_item_with_delay.assert_not_called()


def test_skipped_items_trigger_no_actions_but_still_check_advanced_tooltips(monkeypatch, mocker: MockerFixture, caplog):
    inventory = mocker.Mock()
    slots = [SimpleNamespace(is_junk=False, is_fav=False, center=(0, 0)) for _ in range(3)]
    inventory.get_item_slots.return_value = (slots, [])
    inventory.menu_name = "inventory"
    item = Item(item_type=ItemType.Helm, power=900, affixes=[Affix(name="armor", type=AffixType.greater)])
    monkeypatch.setattr(_filter.src.perception, "read_latest_item", lambda: item)
    monkeypatch.setattr(_filter, "capture", lambda: object())
    monkeypatch.setattr(_filter.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(_filter, "is_ignored_item", lambda _item: False)
    monkeypatch.setattr(
        _filter, "Filter", lambda: SimpleNamespace(should_keep=lambda _item: FilterResult(False, [], True))
    )
    mocker.patch.object(_filter, "is_capture_enabled", return_value=False)
    actions = [
        mocker.patch.object(_filter, name) for name in ("mark_as_favorite", "mark_as_junk", "drop_item_from_inventory")
    ]

    with caplog.at_level(logging.WARNING, logger=_filter.LOGGER.name):
        check_items(inventory, ItemRefreshType.no_refresh)

    for action in actions:
        action.assert_not_called()
    assert "3 out of 3 non-junk rarity items checked had all greater affixes" in caplog.text


def test_mythic_items_are_skipped_when_filter_category_is_disabled(monkeypatch, mocker: MockerFixture):
    inventory = mocker.Mock()
    inventory.get_item_slots.return_value = ([SimpleNamespace(is_junk=False, is_fav=False, center=(0, 0))], [])
    inventory.menu_name = "inventory"
    item = Item(item_type=ItemType.Helm, power=900, rarity=ItemRarity.Mythic)
    settings = SimpleNamespace(
        general=SimpleNamespace(
            filter_equipment=False,
            mark_as_favorite=True,
            do_not_junk_ancestral_legendaries=False,
            auto_use_temper_manuals=False,
            scan_post_hover_sleep=0.0,
        )
    )
    monkeypatch.setattr(_filter, "get_settings", lambda: settings)
    monkeypatch.setattr(_filter.src.perception, "read_latest_item", lambda: item)
    monkeypatch.setattr(_filter, "capture", lambda: object())
    monkeypatch.setattr(_filter.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(_filter, "is_ignored_item", lambda _item: False)
    monkeypatch.setattr(
        _filter, "Filter", lambda: SimpleNamespace(should_keep=lambda _item: FilterResult(False, [], skipped=True))
    )
    mocker.patch.object(_filter, "is_capture_enabled", return_value=False)
    favorite = mocker.patch.object(_filter, "mark_as_favorite")

    check_items(inventory, ItemRefreshType.no_refresh)

    favorite.assert_not_called()


def test_check_items_writes_capture_when_enabled(monkeypatch, mocker: MockerFixture):
    inventory = mocker.Mock()
    slot = SimpleNamespace(is_junk=False, is_fav=False, center=(100, 100))
    inventory.get_item_slots.return_value = ([slot], [])
    inventory.menu_name = "inventory"
    item = Item(item_type=ItemType.Helm, power=900)

    monkeypatch.setattr(_filter.src.perception, "read_latest_item", lambda: item)
    monkeypatch.setattr(_filter, "capture", lambda: object())
    monkeypatch.setattr(_filter.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(_filter, "is_ignored_item", lambda _item: False)
    monkeypatch.setattr(
        _filter, "Filter", lambda: SimpleNamespace(should_keep=lambda _item: FilterResult(False, [], skipped=True))
    )
    mocker.patch.object(_filter, "is_capture_enabled", return_value=True)
    detection = SimpleNamespace(found=True, cropped_descr=object(), failure_reason=None)
    mocker.patch.object(_filter, "find_descr_with_diagnostics", return_value=detection)
    write_capture = mocker.patch.object(_filter, "write_capture")

    check_items(inventory, ItemRefreshType.no_refresh)

    write_capture.assert_called_once()
    bundle = write_capture.call_args.args[0]
    assert bundle.kind == "single"
    assert bundle.source == "filter_check_items"
    assert bundle.items[0].item is item


def test_check_items_skips_capture_when_disabled(monkeypatch, mocker: MockerFixture):
    inventory = mocker.Mock()
    slot = SimpleNamespace(is_junk=False, is_fav=False, center=(100, 100))
    inventory.get_item_slots.return_value = ([slot], [])
    inventory.menu_name = "inventory"
    item = Item(item_type=ItemType.Helm, power=900)

    monkeypatch.setattr(_filter.src.perception, "read_latest_item", lambda: item)
    monkeypatch.setattr(_filter, "capture", lambda: object())
    monkeypatch.setattr(_filter.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(_filter, "is_ignored_item", lambda _item: False)
    monkeypatch.setattr(
        _filter, "Filter", lambda: SimpleNamespace(should_keep=lambda _item: FilterResult(False, [], skipped=True))
    )
    mocker.patch.object(_filter, "is_capture_enabled", return_value=False)
    write_capture = mocker.patch.object(_filter, "write_capture")

    check_items(inventory, ItemRefreshType.no_refresh)

    write_capture.assert_not_called()
