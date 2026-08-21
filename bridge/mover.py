"""File mover: pending -> sent (success) or failed (exhausted retries).

Layout after move:

    ~/.giaoit/captures/sent/<capture_id>/
        payload.json
        *.png

    ~/.giaoit/captures/failed/<capture_id>/
        payload.json
        *.png
"""

import shutil
from pathlib import Path

from bridge.log import get_logger

LOGGER = get_logger()


def move_to_sent(capture_id: str, json_path: Path, image_paths: list[Path], sent_dir: Path) -> Path:
    return _move(capture_id, json_path, image_paths, sent_dir)


def move_to_failed(capture_id: str, json_path: Path, image_paths: list[Path], failed_dir: Path) -> Path:
    return _move(capture_id, json_path, image_paths, failed_dir)


def _move(capture_id: str, json_path: Path, image_paths: list[Path], destination_root: Path) -> Path:
    destination_root.mkdir(parents=True, exist_ok=True)
    target_dir = destination_root / capture_id
    target_dir.mkdir(parents=True, exist_ok=True)

    if json_path.exists():
        shutil.move(str(json_path), str(target_dir / "payload.json"))

    for image in image_paths:
        if not image.exists():
            continue
        shutil.move(str(image), str(target_dir / image.name))

    LOGGER.info("moved capture %s -> %s", capture_id, target_dir)
    return target_dir
