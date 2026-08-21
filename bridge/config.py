"""Runtime configuration for the GiaoIT V1 bridge.

Reads from environment with sensible defaults; override only when needed.
"""

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_RECEIVER_URL = "http://127.0.0.1:8000"
DEFAULT_CAPTURE_DIR = Path.home() / ".giaoit"
DEFAULT_POLL_INTERVAL_SECONDS = 0.5
DEFAULT_STABILITY_SECONDS = 0.3
DEFAULT_MAX_RETRIES = 5
DEFAULT_BACKOFF_BASE_SECONDS = 2.0
DEFAULT_BACKOFF_MAX_SECONDS = 300.0
DEFAULT_LOG_LEVEL = "INFO"


@dataclass(frozen=True)
class BridgeConfig:
    receiver_url: str
    capture_dir: Path
    poll_interval_seconds: float
    stability_seconds: float
    max_retries: int
    backoff_base_seconds: float
    backoff_max_seconds: float
    log_level: str

    @property
    def pending_dir(self) -> Path:
        return self.capture_dir / "captures" / "pending"

    @property
    def sent_dir(self) -> Path:
        return self.capture_dir / "captures" / "sent"

    @property
    def failed_dir(self) -> Path:
        return self.capture_dir / "captures" / "failed"

    @property
    def received_dir(self) -> Path:
        return self.capture_dir / "received"

    @property
    def logs_dir(self) -> Path:
        return self.capture_dir / "logs"

    @property
    def state_dir(self) -> Path:
        return self.capture_dir / "state"

    @property
    def retry_queue_file(self) -> Path:
        return self.state_dir / "retry_queue.json"


def load_config() -> BridgeConfig:
    return BridgeConfig(
        receiver_url=os.environ.get("GIAOIT_RECEIVER_URL", DEFAULT_RECEIVER_URL).rstrip("/"),
        capture_dir=Path(os.environ.get("GIAOIT_CAPTURE_DIR", str(DEFAULT_CAPTURE_DIR))).expanduser(),
        poll_interval_seconds=float(os.environ.get("GIAOIT_POLL_INTERVAL", DEFAULT_POLL_INTERVAL_SECONDS)),
        stability_seconds=float(os.environ.get("GIAOIT_STABILITY_SECONDS", DEFAULT_STABILITY_SECONDS)),
        max_retries=int(os.environ.get("GIAOIT_MAX_RETRIES", DEFAULT_MAX_RETRIES)),
        backoff_base_seconds=float(os.environ.get("GIAOIT_BACKOFF_BASE", DEFAULT_BACKOFF_BASE_SECONDS)),
        backoff_max_seconds=float(os.environ.get("GIAOIT_BACKOFF_MAX", DEFAULT_BACKOFF_MAX_SECONDS)),
        log_level=os.environ.get("GIAOIT_LOG_LEVEL", DEFAULT_LOG_LEVEL),
    )
