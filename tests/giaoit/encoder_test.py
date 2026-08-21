"""Tests for src.giaoit.encoder.build_payload."""

import json

from src.game_data import ItemRarity, ItemType
from src.giaoit.encoder import SCHEMA, build_payload
from src.giaoit.models import CaptureBundle, CapturedItem, CaptureMeta
from src.item import Affix, AffixType, Aspect, Item


def _make_item() -> Item:
    return Item(
        item_type=ItemType.ChestArmor,
        rarity=ItemRarity.Legendary,
        power=925,
        is_ancestral=True,
        affixes=[
            Affix(name="armor", text="+45 Armor", value=45.0, min_value=0.0, max_value=100.0, type=AffixType.normal),
            Affix(
                name="crit_chance",
                text="+7.5% Critical Strike Chance [GA]",
                value=7.5,
                min_value=5.0,
                max_value=8.0,
                type=AffixType.greater,
            ),
        ],
        inherent=[
            Affix(name="inherent_int", text="+330 Intelligence", value=330.0, type=AffixType.inherent),
        ],
        aspect=Aspect(name="aspect_iron_maelstrom", text="...", value=None, min_value=None, max_value=None),
    )


def _meta() -> CaptureMeta:
    return CaptureMeta(capture_id="abc123", captured_at="2026-08-12T00:00:00+00:00", machine_id="m1")


def test_single_payload_has_all_outer_fields() -> None:
    bundle = CaptureBundle(kind="single", items=[CapturedItem(item=_make_item(), image=None)], source="f2_key")
    payload = build_payload(bundle, _meta())

    assert payload["schema"] == SCHEMA == "giaoit.capture.v1"
    assert payload["kind"] == "single"
    assert payload["capture_id"] == "abc123"
    assert payload["captured_at"] == "2026-08-12T00:00:00+00:00"
    assert payload["machine_id"] == "m1"
    assert payload["source"] == "f2_key"
    assert "stash_info" not in payload


def test_stash_payload_has_stash_info() -> None:
    bundle = CaptureBundle(
        kind="stash",
        items=[CapturedItem(item=_make_item(), image=None)],
        source="f4_key",
        stash_tabs_scanned=[0, 1],
    )
    payload = build_payload(bundle, _meta())

    assert payload["kind"] == "stash"
    assert payload["stash_info"] == {"tabs_scanned": [0, 1]}


def test_item_serialises_via_item_json_encoder() -> None:
    bundle = CaptureBundle(kind="single", items=[CapturedItem(item=_make_item(), image=None)], source="f2_key")
    payload = build_payload(bundle, _meta())

    item_dict = payload["items"][0]["item"]
    assert item_dict["item_type"] == ItemType.ChestArmor.value
    assert item_dict["rarity"] == ItemRarity.Legendary.value
    assert item_dict["power"] == 925
    assert item_dict["is_ancestral"] is True
    assert item_dict["set_name"] is None
    assert item_dict["name"] is None
    assert len(item_dict["affixes"]) == 2


def test_affix_type_serialises_as_string_enum() -> None:
    bundle = CaptureBundle(kind="single", items=[CapturedItem(item=_make_item(), image=None)], source="f2_key")
    payload = build_payload(bundle, _meta())

    affixes = payload["items"][0]["item"]["affixes"]
    types = sorted(a["type"] for a in affixes)
    assert "greater" in types
    assert "normal" in types
    assert all(isinstance(t, str) for t in types)


def test_image_file_field_round_trips() -> None:
    bundle = CaptureBundle(
        kind="single",
        items=[CapturedItem(item=_make_item(), image=object(), image_file="abc123.png")],
        source="f2_key",
    )
    payload = build_payload(bundle, _meta())

    assert payload["items"][0]["image_file"] == "abc123.png"


def test_none_item_type_serialises_to_null() -> None:
    item = Item(item_type=None, rarity=None, power=None)
    bundle = CaptureBundle(kind="single", items=[CapturedItem(item=item, image=None)], source="f2_key")
    payload = build_payload(bundle, _meta())

    assert payload["items"][0]["item"]["item_type"] is None
    assert payload["items"][0]["item"]["rarity"] is None


def test_payload_is_json_serialisable() -> None:
    bundle = CaptureBundle(
        kind="stash",
        items=[CapturedItem(item=_make_item(), image=None)],
        source="f4_key",
        stash_tabs_scanned=[0],
    )
    payload = build_payload(bundle, _meta())

    text = json.dumps(payload, ensure_ascii=False)
    parsed = json.loads(text)
    assert parsed["schema"] == "giaoit.capture.v1"


def test_single_payload_has_item_hash() -> None:
    bundle = CaptureBundle(kind="single", items=[CapturedItem(item=_make_item(), image=None)], source="f2_key")
    payload = build_payload(bundle, _meta())

    assert "item_hash" in payload
    assert isinstance(payload["item_hash"], str)
    assert len(payload["item_hash"]) == 64  # sha-256 hex


def test_stash_payload_has_no_item_hash() -> None:
    bundle = CaptureBundle(
        kind="stash",
        items=[CapturedItem(item=_make_item(), image=None)],
        source="f4_key",
        stash_tabs_scanned=[0],
    )
    payload = build_payload(bundle, _meta())

    assert "item_hash" not in payload


def test_item_hash_stable_for_same_content() -> None:
    from src.giaoit.encoder import item_hash

    h1 = item_hash(_make_item())
    h2 = item_hash(_make_item())
    assert h1 == h2


def test_item_hash_changes_when_value_changes() -> None:
    from src.giaoit.encoder import item_hash

    base = _make_item()
    other = Item(
        item_type=base.item_type,
        rarity=base.rarity,
        power=999,
        affixes=base.affixes,
    )
    assert item_hash(base) != item_hash(other)


def test_item_hash_independent_of_shop_state() -> None:
    """is_in_shop is transient — same item read in shop vs not must hash equal."""
    from src.giaoit.encoder import item_hash

    in_shop = _make_item()
    in_shop.is_in_shop = True
    not_in_shop = _make_item()
    not_in_shop.is_in_shop = False

    assert item_hash(in_shop) == item_hash(not_in_shop)
