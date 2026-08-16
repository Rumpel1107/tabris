import config
import json
import logging
import os

from datetime import datetime, time, timedelta, timezone

from core.db import get_user_records

logger = logging.getLogger(__name__)


def deletion_deadline(deactivated_at: str) -> datetime:
    """Return when a deactivated account's data is erased, as an aware UTC datetime.

    The policy is stated in whole days, so the deadline is the end of the last day rather
    than the hour of the request: the date shown to the user is a date they fully get.
    SQLite writes the mark with its own clock in UTC and no offset, so it reads back as UTC.
    """
    marked = datetime.fromisoformat(deactivated_at).replace(tzinfo=timezone.utc)
    last_day = marked.date() + timedelta(days=config.ACCOUNT_GRACE_DAYS)
    return datetime.combine(last_day, time.max, tzinfo=timezone.utc)


def _safe_name(name: str) -> str:
    """Reduce a display name to characters that cannot alter a file path."""
    hyphenated = "-".join(name.split())
    return "".join(char for char in hyphenated if char.isalnum() or char in "-_").strip("-")


def export_user(db_path: str, user_id: int) -> str:
    """Write everything stored about one user to a JSON file and return its path.

    The id leads the file name so the file stays findable after a profile rename.
    """
    records = get_user_records(db_path, user_id)
    if records["user"] is None:
        raise ValueError(f"No user with id {user_id}")
    safe_name = _safe_name(records["user"]["name"])
    filename = f"user-{user_id}-{safe_name}.json" if safe_name else f"user-{user_id}.json"
    os.makedirs(config.EXPORTS_DIR, mode=0o700, exist_ok=True)
    os.chmod(config.EXPORTS_DIR, 0o700)  # makedirs' mode only applies on creation; an existing directory keeps its own
    path = os.path.join(config.EXPORTS_DIR, filename)
    with open(path, "w") as export_file:
        json.dump(records, export_file, ensure_ascii=False, indent=2)
    # personal data in plain text: readable by its owner only, like the database and .env
    os.chmod(path, 0o600)
    logger.info(f"export: user {user_id} written to {path}")
    return path
