"""Read the account list from ~/.giaoit/accounts.txt for the confirm UI."""

from pathlib import Path

from bridge.log import get_logger

LOGGER = get_logger()
DEFAULT_ACCOUNTS_FILE = Path.home() / ".giaoit" / "accounts.txt"


def load_accounts(path: Path | None = None) -> list[str]:
    target = path or DEFAULT_ACCOUNTS_FILE
    if not target.exists():
        LOGGER.warning("accounts file %s missing; UI will show no accounts until you create it", target)
        return []
    try:
        lines = [line.strip() for line in target.read_text(encoding="utf-8").splitlines()]
    except OSError:
        LOGGER.exception("failed to read accounts file %s", target)
        return []
    return [line for line in lines if line and not line.startswith("#")]
