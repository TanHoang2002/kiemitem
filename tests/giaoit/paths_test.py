"""Tests for src.giaoit.paths."""

import importlib

from src.giaoit import paths as giaoit_paths


def test_paths_default_under_home(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GIAOIT_CAPTURE_DIR", str(tmp_path))
    importlib.reload(giaoit_paths)

    assert giaoit_paths.root_dir() == tmp_path
    assert giaoit_paths.captures_root() == tmp_path / "captures"
    assert giaoit_paths.machine_id_file() == tmp_path / "machine_id"
    assert giaoit_paths.accounts_file() == tmp_path / "accounts.txt"


def test_pending_dir_creates_folder(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GIAOIT_CAPTURE_DIR", str(tmp_path))
    importlib.reload(giaoit_paths)

    pending = giaoit_paths.pending_dir()
    assert pending.exists()
    assert pending.is_dir()

    before = pending.stat().st_mtime_ns
    pending_again = giaoit_paths.pending_dir()
    assert pending_again == pending
    assert pending.exists()


def test_all_dirs_are_idempotent(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GIAOIT_CAPTURE_DIR", str(tmp_path))
    importlib.reload(giaoit_paths)

    for fn in (giaoit_paths.pending_dir, giaoit_paths.sent_dir, giaoit_paths.failed_dir):
        path = fn()
        assert path.exists()
        fn()
        assert path.exists()


def test_retry_queue_file_under_state(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GIAOIT_CAPTURE_DIR", str(tmp_path))
    importlib.reload(giaoit_paths)

    queue = giaoit_paths.retry_queue_file()
    assert queue.parent.exists()
    assert queue.name == "retry_queue.json"


def teardown_module(module) -> None:
    """Reset module-level cache so other tests start from a clean env state."""
    importlib.reload(giaoit_paths)
