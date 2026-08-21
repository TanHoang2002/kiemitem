"""GiaoIT V1 runtime configuration: machine identity and master switch."""

import logging
import os
import uuid

from src.giaoit.paths import machine_id_file

LOGGER = logging.getLogger(__name__)

KILL_SWITCH_ENV = "GIAOIT_DISABLED"

_cached_machine_id: str | None = None


def machine_id() -> str:
    """Return a stable per-machine identifier, generating and caching it on first call."""
    global _cached_machine_id
    if _cached_machine_id is not None:
        return _cached_machine_id

    path = machine_id_file()
    if path.exists():
        try:
            value = path.read_text(encoding="utf-8").strip()
        except OSError:
            LOGGER.exception("Failed to read machine_id file at %s; generating a new one", path)
            value = ""
        if value:
            _cached_machine_id = value
            return value

    new_id = uuid.uuid4().hex
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(new_id + "\n", encoding="utf-8")
    except OSError:
        LOGGER.exception("Failed to persist machine_id file at %s; will use in-memory value", path)
    _cached_machine_id = new_id
    return new_id


def is_kill_switch_active() -> bool:
    """Return True when the GIAOIT_DISABLED env var is set to a truthy value."""
    raw = os.environ.get(KILL_SWITCH_ENV, "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def is_capture_enabled() -> bool:
    """Return True only when both the master setting is on and the kill switch is off.

    The master ``general.capture_mode`` flag is read lazily here (instead of being
    passed in) so call sites — notably the filter hot loop — stay simple.
    """
    if is_kill_switch_active():
        return False

    try:
        from src.settings import get_settings

        return bool(get_settings().general.capture_mode)
    except Exception:
        LOGGER.exception("Failed to read capture_mode setting; treating as disabled")
        return False


def reset_cache_for_tests() -> None:
    """Clear the in-memory machine_id cache. Tests only."""
    global _cached_machine_id
    _cached_machine_id = None
