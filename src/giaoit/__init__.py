"""GiaoIT V1 capture pipeline public interface.

This package adds a *side-channel* capture output to d4lf without changing
the upstream filter behaviour: every item read by ``check_items`` (and every
explicit F2/F4 hotkey press) writes a JSON payload + cropped tooltip image
to ``~/.giaoit/captures/pending/`` so an external bridge process can pick
them up.
"""

from src.giaoit.config import is_capture_enabled, machine_id
from src.giaoit.models import CaptureBundle, CapturedItem, CaptureKind, CaptureMeta, CaptureSource

__all__ = [
    "CaptureBundle",
    "CaptureKind",
    "CaptureMeta",
    "CaptureSource",
    "CapturedItem",
    "is_capture_enabled",
    "machine_id",
]
