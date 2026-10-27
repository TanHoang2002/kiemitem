"""Dataclasses passed between capture, encoder and writer stages."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import numpy as np

    from src.item.models import Item

CaptureKind = Literal["single", "stash", "currency"]
CaptureSource = Literal["f2_key", "f4_key", "filter_check_items", "auto_scan"]


@dataclass
class CapturedItem:
    """A single read item paired with its cropped tooltip image."""

    item: Item
    image: np.ndarray | None
    image_file: str | None = None


@dataclass
class CaptureBundle:
    """Output of a capture pass — one item for F2, many for F4."""

    kind: CaptureKind
    items: list[CapturedItem]
    source: CaptureSource
    stash_tabs_scanned: list[int] = field(default_factory=list)


@dataclass
class CaptureMeta:
    """Metadata written alongside every capture payload."""

    capture_id: str
    captured_at: str
    machine_id: str
