import config
import logging
import os
import pytest
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db import create_user, get_user, init_db
from tools import backup
from tools.backup import create_backup


def test_writes_a_copy_named_by_date(tmp_path):
    db_path = str(tmp_path / "tabris.db")
    init_db(db_path)
    create_user(db_path, "Ana")
    backup_dir = tmp_path / "backups"

    path = create_backup(db_path, str(backup_dir), now=datetime(2026, 8, 18))

    assert path == str(backup_dir / "tabris-2026-08-18.db")
    assert get_user(path, 1)["name"] == "Ana"


def test_creates_the_copy_owner_only(tmp_path):
    db_path = str(tmp_path / "tabris.db")
    init_db(db_path)
    backup_dir = tmp_path / "backups"

    path = create_backup(db_path, str(backup_dir))

    assert os.stat(path).st_mode & 0o777 == 0o600
    assert os.stat(backup_dir).st_mode & 0o777 == 0o700


def test_keeps_only_the_seven_most_recent_copies(tmp_path):
    db_path = str(tmp_path / "tabris.db")
    init_db(db_path)
    backup_dir = tmp_path / "backups"
    for day in range(1, 10):
        create_backup(db_path, str(backup_dir), now=datetime(2026, 8, day))

    remaining = sorted(entry.name for entry in backup_dir.iterdir())

    assert remaining == [f"tabris-2026-08-0{day}.db" for day in range(3, 10)]


def test_rotation_leaves_unrelated_files_alone(tmp_path):
    db_path = str(tmp_path / "tabris.db")
    init_db(db_path)
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    (backup_dir / "notes.txt").write_text("keep me")
    for day in range(1, 10):
        create_backup(db_path, str(backup_dir), now=datetime(2026, 8, day))

    assert (backup_dir / "notes.txt").read_text() == "keep me"


def test_verify_rejects_a_file_sqlite_cannot_read(tmp_path):
    broken = tmp_path / "broken.db"
    broken.write_bytes(b"not a database")

    assert backup._verify(str(broken)) is False


def test_removes_a_copy_that_does_not_verify(tmp_path, monkeypatch):
    db_path = str(tmp_path / "tabris.db")
    init_db(db_path)
    backup_dir = tmp_path / "backups"
    monkeypatch.setattr(backup, "_verify", lambda path: False)

    with pytest.raises(RuntimeError):
        create_backup(db_path, str(backup_dir), now=datetime(2026, 8, 18))

    assert list(backup_dir.iterdir()) == []


def test_main_writes_a_backup_and_reports_success(tmp_path, monkeypatch):
    db_path = str(tmp_path / "tabris.db")
    init_db(db_path)
    monkeypatch.setattr(config, "DB_PATH", db_path)
    backup_dir = tmp_path / "backups"

    assert backup.main([str(backup_dir)]) == 0
    assert len(list(backup_dir.iterdir())) == 1


def test_main_reports_failure_instead_of_raising(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "missing" / "tabris.db"))

    with caplog.at_level(logging.ERROR):
        result = backup.main([str(tmp_path / "backups")])

    assert result == 1
    assert "backup failed" in caplog.text
