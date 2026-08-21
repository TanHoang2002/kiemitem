"""Bridge entry point: spin up watcher + dispatcher + retry sweeper.

Default mode runs headless (auto-accept with first account for single
captures). Pass ``--ui`` to enable the Tk confirm window.

Run::

    python -m bridge.main --ui
    python -m bridge.main --headless
"""

import argparse
import signal
import sys
import threading
from pathlib import Path

from bridge.config import BridgeConfig, load_config
from bridge.dispatcher import Dispatcher
from bridge.log import configure_logging
from bridge.retry_queue import RetryQueue
from bridge.watcher import build_watcher


def _ensure_dirs(config: BridgeConfig) -> None:
    for path in (
        config.pending_dir,
        config.sent_dir,
        config.failed_dir,
        config.received_dir,
        config.logs_dir,
        config.state_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)


def _load_confirm_fn(use_ui: bool):
    if not use_ui:
        return None
    try:
        from bridge.confirm_ui import run_confirm_loop
    except Exception:
        return None
    return run_confirm_loop


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GiaoIT V1 bridge")
    parser.add_argument("--ui", action="store_true", help="enable Tk confirm window (default: headless)")
    parser.add_argument("--headless", action="store_true", help="disable UI even if Tk is available")
    parser.add_argument("--once", action="store_true", help="scan once and exit (testing)")
    args = parser.parse_args(argv)

    config = load_config()
    _ensure_dirs(config)
    logger = configure_logging(config.logs_dir, config.log_level)
    logger.info("bridge starting up; receiver=%s capture_dir=%s", config.receiver_url, config.capture_dir)

    retry_queue = RetryQueue(config.retry_queue_file)
    confirm_fn = _load_confirm_fn(use_ui=args.ui and not args.headless)
    dispatcher = Dispatcher(config=config, retry_queue=retry_queue, confirm_fn=confirm_fn)

    watcher = build_watcher(config, dispatcher.handle)

    stop_event = threading.Event()

    def _handle_signal(signum, _frame) -> None:
        logger.info("received signal %s; shutting down", signum)
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    if args.once:
        ready = watcher.scan_once()
        logger.info("one-shot scan found %d files", len(ready))
        for path in ready:
            dispatcher.handle(path)
        return 0

    watcher.start()

    # Retry sweeper — periodic background thread.
    def _sweep() -> None:
        while not stop_event.is_set():
            try:
                for entry in retry_queue.due(config.max_retries):
                    dispatcher.handle_retry(entry)
                for entry in retry_queue.exhausted(config.max_retries):
                    logger.error("giving up on %s after %d retries", entry["capture_id"], entry["retry_count"])
                    move_exhausted(config, entry, dispatcher)
            except Exception:
                logger.exception("sweeper pass crashed")
            stop_event.wait(config.poll_interval_seconds)

    sweeper = threading.Thread(target=_sweep, daemon=True, name="giaoit-sweeper")
    sweeper.start()

    # UI mainloop if requested; otherwise block on signal.
    if confirm_fn is not None and hasattr(confirm_fn, "mainloop"):
        try:
            confirm_fn.mainloop(stop_event)  # type: ignore[attr-defined]
        except AttributeError:
            stop_event.wait()
    else:
        stop_event.wait()

    watcher.stop()
    logger.info("bridge stopped cleanly")
    return 0


def move_exhausted(config: BridgeConfig, entry: dict, dispatcher: Dispatcher) -> None:
    from bridge.mover import move_to_failed

    json_path = Path(entry["json_path"])
    image_paths = [Path(p) for p in entry.get("image_paths", [])]
    move_to_failed(entry["capture_id"], json_path, image_paths, config.failed_dir)
    dispatcher._retry_queue.remove(entry["capture_id"])


if __name__ == "__main__":
    sys.exit(main())
