"""Tests for src.giaoit.runner."""

import importlib
from types import SimpleNamespace

from src.giaoit import runner as giaoit_runner


def _reload(monkeypatch, tmp_path):
    monkeypatch.setenv("GIAOIT_CAPTURE_DIR", str(tmp_path))
    importlib.reload(giaoit_runner)
    return giaoit_runner


def test_run_capture_single_noops_when_disabled(monkeypatch, tmp_path) -> None:
    r = _reload(monkeypatch, tmp_path)
    monkeypatch.setattr(r, "is_capture_enabled", lambda: False)
    capture_called = mocker_call(r, "capture_item_at_cursor")
    write_called = mocker_call(r, "write_capture")

    r.run_capture_single()

    assert capture_called["count"] == 0
    assert write_called["count"] == 0


def test_run_capture_single_calls_capture_and_write(monkeypatch, tmp_path) -> None:
    r = _reload(monkeypatch, tmp_path)
    monkeypatch.setattr(r, "is_capture_enabled", lambda: True)
    bundle = SimpleNamespace(kind="single")
    monkeypatch.setattr(r, "capture_item_at_cursor", lambda: bundle)

    calls: list = []
    monkeypatch.setattr(r, "write_capture", lambda b: calls.append(b))

    r.run_capture_single()

    assert calls == [bundle]


def test_run_capture_single_skips_write_when_no_bundle(monkeypatch, tmp_path) -> None:
    r = _reload(monkeypatch, tmp_path)
    monkeypatch.setattr(r, "is_capture_enabled", lambda: True)
    monkeypatch.setattr(r, "capture_item_at_cursor", lambda: None)
    write_called = mocker_call(r, "write_capture")

    r.run_capture_single()

    assert write_called["count"] == 0


def test_run_capture_stash_noops_when_disabled(monkeypatch, tmp_path) -> None:
    r = _reload(monkeypatch, tmp_path)
    monkeypatch.setattr(r, "is_capture_enabled", lambda: False)
    capture_called = mocker_call(r, "read_full_stash")
    write_called = mocker_call(r, "write_capture")

    r.run_capture_stash()

    assert capture_called["count"] == 0
    assert write_called["count"] == 0


def mocker_call(module, name):
    """Tiny helper to record call counts without pytest-mock available here."""
    state = {"count": 0}

    def _fn(*_args, **_kwargs):
        state["count"] += 1

    setattr(module, name, _fn)
    return state


def teardown_module(module) -> None:
    importlib.reload(giaoit_runner)
