"""Filesystem layout for GiaoIT V1 capture output.

All tool-side captures land under ``~/.giaoit`` (overridable via the
``GIAOIT_CAPTURE_DIR`` environment variable for tests).
"""

import os
import pathlib

GIAOIT_DIR_ENV = "GIAOIT_CAPTURE_DIR"
_DEFAULT_DIR_NAME = ".giaoit"


def root_dir() -> pathlib.Path:
    """Root directory for all GiaoIT runtime state."""
    override = os.environ.get(GIAOIT_DIR_ENV)
    if override:
        return pathlib.Path(override).expanduser()
    return pathlib.Path.home() / _DEFAULT_DIR_NAME


def machine_id_file() -> pathlib.Path:
    return root_dir() / "machine_id"


def accounts_file() -> pathlib.Path:
    return root_dir() / "accounts.txt"


def captures_root() -> pathlib.Path:
    return root_dir() / "captures"


def pending_dir() -> pathlib.Path:
    path = captures_root() / "pending"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sent_dir() -> pathlib.Path:
    path = captures_root() / "sent"
    path.mkdir(parents=True, exist_ok=True)
    return path


def failed_dir() -> pathlib.Path:
    path = captures_root() / "failed"
    path.mkdir(parents=True, exist_ok=True)
    return path


def received_dir() -> pathlib.Path:
    path = root_dir() / "received"
    path.mkdir(parents=True, exist_ok=True)
    return path


def logs_dir() -> pathlib.Path:
    path = root_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def state_dir() -> pathlib.Path:
    path = root_dir() / "state"
    path.mkdir(parents=True, exist_ok=True)
    return path


def retry_queue_file() -> pathlib.Path:
    return state_dir() / "retry_queue.json"
