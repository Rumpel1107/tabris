import config
import glob
import json
import logging
import os

from core.db import deactivate_user, delete_messages_before, delete_user_completely, get_deactivated_users, get_user, get_user_records, reactivate_user
from datetime import datetime, time, timedelta, timezone

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


def _export_paths(user_id: int) -> list[str]:
    """Return every export file belonging to one user, found by the id leading the name.

    Matching on the id rather than rebuilding the file name keeps the file findable after
    a profile rename, which is what that name format is for.
    """
    return sorted(
        glob.glob(os.path.join(config.EXPORTS_DIR, f"user-{user_id}.json"))
        + glob.glob(os.path.join(config.EXPORTS_DIR, f"user-{user_id}-*.json"))
    )


def deactivate_account(db_path: str, user_id: int) -> str:
    """Deactivate a user, but only after their data export succeeds.

    Export runs first on purpose: if it raises, deactivate_user never runs and the
    account stays active — nobody is deactivated without leaving with their copy (AC4).
    """
    path = export_user(db_path, user_id)
    deactivate_user(db_path, user_id)
    logger.info(f"deactivate: user {user_id} marked deactivated")
    return path


def reactivate_account(db_path: str, user_id: int) -> list[str]:
    """Destroy a user's export files and clear their deactivation mark, returning the files removed.

    The export dies with the grace window, so it is destroyed first: a failed delete leaves the
    account deactivated instead of active with its personal data still on disk — the mirror of
    deactivate_account's order. A missing file is not a failure; it is already the wanted state.
    """
    removed = _export_paths(user_id)
    for path in removed:
        os.remove(path)
    reactivate_user(db_path, user_id)
    logger.info(f"reactivate: user {user_id} restored, {len(removed)} export file(s) destroyed")
    return removed


def _erase(db_path: str, user_id: int) -> None:
    """Destroy a user's export files and then their rows, in that order.

    Same order as reactivate_account and for the same reason: a failed file delete leaves the
    account deactivated and retryable, instead of erasing the rows and orphaning the copy.
    """
    for path in _export_paths(user_id):
        os.remove(path)
    delete_user_completely(db_path, user_id)


def purge_due_accounts(db_path: str, now: datetime | None = None) -> list[int]:
    """Erase every deactivated account whose grace window has ended and return the ids erased.

    Meant to run unattended, so it asks nothing and touches nothing still inside its window.
    `now` is injectable to keep the rule testable; when the window ends is deletion_deadline's
    call alone, so the policy has one owner.
    """
    moment = now or datetime.now(timezone.utc)
    purged = []
    for account in get_deactivated_users(db_path):
        if deletion_deadline(account["deactivated_at"]) > moment:
            continue
        _erase(db_path, account["id"])
        purged.append(account["id"])
    logger.info(f"purge: {len(purged)} account(s) erased")
    return purged


def purge_old_messages(db_path: str, now: datetime | None = None) -> int:
    """Erase conversation past the retention window and return how many messages were erased.

    `now` is injectable for the same reason as in purge_due_accounts: the window is the policy,
    and it has one owner.
    """
    moment = now or datetime.now(timezone.utc)
    cutoff = moment - timedelta(days=config.MESSAGE_RETENTION_DAYS)
    erased = delete_messages_before(db_path, cutoff.strftime("%Y-%m-%d %H:%M:%S"))
    logger.info(f"retention: {erased} message(s) erased")
    return erased


def purge_account(db_path: str, user_id: int, ignore_deadline: bool = False) -> None:
    """Erase one account by hand, refusing anything the automatic pass would not have taken.

    An account that is not deactivated is never erased. One still inside its window is erased
    only when the operator says so explicitly — the window is a courtesy to the person, and
    they are the ones who can waive it.
    """
    user = get_user(db_path, user_id)
    if user is None:
        raise ValueError(f"No user with id {user_id}")
    if user["deactivated_at"] is None:
        raise ValueError(f"User {user_id} is not deactivated: deactivate the account first")
    deadline = deletion_deadline(user["deactivated_at"])
    if deadline > datetime.now(timezone.utc) and not ignore_deadline:
        raise ValueError(f"User {user_id} is still inside their grace window, until {deadline:%Y-%m-%d}")
    _erase(db_path, user_id)
    logger.info(f"purge: user {user_id} erased by hand")
