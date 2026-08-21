"""Build the JSON payload for a capture bundle.

We extend d4lf's ``ItemJSONEncoder`` for most Item fields (V1 section 4 schema).
The upstream encoder dumps affixes via ``Affix.__dict__`` which leaves
``AffixType`` enum values unserialised — it was never actually called in d4lf.
Rather than touch upstream, we subclass and convert enum members to their names.
"""

import enum
import hashlib
import json

from src.giaoit.models import CaptureBundle, CaptureMeta
from src.item.models import Item, ItemJSONEncoder

SCHEMA = "giaoit.capture.v1"


class _GiaoitEncoder(ItemJSONEncoder):
    """ItemJSONEncoder + enum handling for ``Affix.type``."""

    def default(self, o: object) -> object:
        if isinstance(o, enum.Enum):
            return o.name
        return super().default(o)


def _item_to_dict(item: Item) -> dict[str, object]:
    """Serialise an Item to a plain dict via the extended encoder."""
    return json.loads(json.dumps(item, cls=_GiaoitEncoder))


def _stable_affix_signature(affix) -> tuple[object, ...]:
    """Identity tuple for one affix — order-insensitive fields excluded (loc)."""
    return (
        affix.name,
        affix.text,
        affix.value,
        affix.min_value,
        affix.max_value,
        affix.type.name if hasattr(affix.type, "name") else str(affix.type),
    )


def item_hash(item: Item) -> str:
    """Stable SHA-256 hash of an Item's identity-relevant fields.

    Used as a secondary dedup key on the receiver: same item hovered twice
    produces the same hash, so the second capture is dropped (V1 trial #5
    extends to "same item, different capture_id").

    Identity = item_type + rarity + name + power + affixes + inherent + aspect.
    Excludes transient state (is_in_shop, codex_upgrade, cosmetic_upgrade) so
    the same physical item read from different contexts still hashes equally.
    """
    payload = {
        "item_type": item.item_type.value if item.item_type else None,
        "rarity": item.rarity.value if item.rarity else None,
        "name": item.name,
        "power": item.power,
        "is_ancestral": item.is_ancestral,
        "set": item.set,
        "affixes": [_stable_affix_signature(a) for a in item.affixes],
        "inherent": [_stable_affix_signature(a) for a in item.inherent],
        "aspect": (
            None
            if item.aspect is None
            else (
                item.aspect.name,
                item.aspect.text,
                item.aspect.value,
                item.aspect.min_value,
                item.aspect.max_value,
            )
        ),
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def bundle_hash(bundle: CaptureBundle) -> str | None:
    """Hash for a single-item bundle. Returns None for multi-item (stash) bundles.

    Stash captures contain many items and dedup-by-content there is awkward
    (partial overlap, ordering). V1 leaves that to capture_id only.
    """
    if bundle.kind != "single" or len(bundle.items) != 1:
        return None
    return item_hash(bundle.items[0].item)


def build_payload(bundle: CaptureBundle, meta: CaptureMeta) -> dict[str, object]:
    """Assemble the full payload dict written to ``pending/<capture_id>.json``."""
    items_payload: list[dict[str, object]] = []
    for captured in bundle.items:
        items_payload.append(
            {
                "image_file": captured.image_file,
                "item": _item_to_dict(captured.item),
            }
        )

    payload: dict[str, object] = {
        "schema": SCHEMA,
        "kind": bundle.kind,
        "capture_id": meta.capture_id,
        "captured_at": meta.captured_at,
        "machine_id": meta.machine_id,
        "source": bundle.source,
        "items": items_payload,
    }
    if bundle.kind == "single":
        payload["item_hash"] = bundle_hash(bundle)
    if bundle.kind == "stash":
        payload["stash_info"] = {"tabs_scanned": list(bundle.stash_tabs_scanned)}
    return payload
