import argparse
import config
import contextlib
import glob
import logging
import os
import sqlite3
import sys
from datetime import datetime

logger = logging.getLogger(__name__)


def create_backup(db_path: str, backup_dir: str, now: datetime | None = None) -> str:
    """Copy the database into backup_dir under a date-stamped name and return the copy's path."""
    now = now or datetime.now()
    os.makedirs(backup_dir, mode=0o700, exist_ok=True)
    stem = os.path.splitext(os.path.basename(db_path))[0]
    path = os.path.join(backup_dir, f"{stem}-{now:%Y-%m-%d}.db")
    with contextlib.closing(sqlite3.connect(db_path)) as source:
        with contextlib.closing(sqlite3.connect(path)) as copy:
            source.backup(copy)
    if not _verify(path):
        os.remove(path)
        raise RuntimeError(f"backup did not verify: {path}")
    os.chmod(path, 0o600)  # sqlite creates the file with the process umask, and a backup travels further than the original
    _rotate(backup_dir, stem)
    return path


def _verify(path: str) -> bool:
    """Open the copy and let SQLite check it, so a corrupt backup never takes a slot in the rotation."""
    try:
        with contextlib.closing(sqlite3.connect(path)) as conn:
            return conn.execute("PRAGMA quick_check").fetchone()[0] == "ok"
    except sqlite3.DatabaseError:
        return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write a dated copy of the database and keep only the most recent ones.",
    )
    parser.add_argument(
        "backup_dir",
        help="Directory the copies are written to. Keep it outside the deployment directory.",
    )
    return parser


def main(argv=None) -> int:
    """Run one backup, reporting the outcome as an exit code so the scheduler records a failed run."""
    args = build_parser().parse_args(argv)
    try:
        path = create_backup(config.DB_PATH, args.backup_dir)
    except Exception:
        logger.exception("backup failed")
        return 1
    logger.info("backup written: %s", path)
    return 0


def _rotate(backup_dir: str, stem: str) -> None:
    """Delete the oldest copies, keeping the most recent config.BACKUPS_KEPT."""
    copies = sorted(glob.glob(os.path.join(backup_dir, f"{stem}-*.db")))  # the date format sorts chronologically as text
    for old in copies[:-config.BACKUPS_KEPT]:
        os.remove(old)


if __name__ == "__main__":
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    sys.exit(main())