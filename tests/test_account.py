import json
import os
import pytest
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.account import deactivate_account, export_user, reactivate_account
from core.db import create_user, create_user_with_channel, deactivate_fact, deactivate_message, get_user, init_db, save_fact, save_message, update_user_profile


@pytest.mark.parametrize("name, expected", [
    ("Ana Maria", "user-{id}-Ana-Maria.json"),
    ("Ana/Maria", "user-{id}-AnaMaria.json"),
    ("🙂", "user-{id}.json"),
])
def test_export_file_name_is_safe_and_led_by_the_id(name, expected):
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        exports_dir = os.path.join(tmp, "exports")
        init_db(db_path)
        user_id = create_user_with_channel(db_path, name, "cli", "key-1")

        with patch("core.account.config.EXPORTS_DIR", exports_dir):
            path = export_user(db_path, user_id)

        assert os.path.basename(path) == expected.format(id=user_id)
        assert os.path.dirname(path) == exports_dir


def test_export_writes_every_record_without_channel_keys():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        exports_dir = os.path.join(tmp, "exports")
        init_db(db_path)
        user_id = create_user_with_channel(db_path, "Ana", "discord", "key-123", language="es")
        retired_id = save_fact(db_path, user_id, "likes tea")
        deactivate_fact(db_path, user_id, retired_id)
        save_fact(db_path, user_id, "lives in Panama")
        undone_id = save_message(db_path, user_id, "assistant", "a reply never read")
        deactivate_message(db_path, user_id, undone_id)
        save_message(db_path, user_id, "user", "hola")

        with patch("core.account.config.EXPORTS_DIR", exports_dir):
            path = export_user(db_path, user_id)

        with open(path) as export_file:
            exported = json.load(export_file)

        assert exported["user"]["name"] == "Ana"
        assert {fact["content"] for fact in exported["facts"]} == {"likes tea", "lives in Panama"}
        assert {message["content"] for message in exported["messages"]} == {"a reply never read", "hola"}
        assert exported["channels"] == ["discord"]
        assert "key-123" not in json.dumps(exported)
        assert oct(os.stat(path).st_mode)[-3:] == "600"


def test_deactivate_account_writes_an_export_and_marks_deactivated():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        exports_dir = os.path.join(tmp, "exports")
        init_db(db_path)
        user_id = create_user(db_path, "Rumpel", "es")

        with patch("core.account.config.EXPORTS_DIR", exports_dir):
            path = deactivate_account(db_path, user_id)

        assert os.path.exists(path)
        assert get_user(db_path, user_id)["deactivated_at"] is not None


def test_deactivate_account_leaves_the_account_active_when_export_fails():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        init_db(db_path)
        user_id = create_user(db_path, "Rumpel", "es")

        with patch("core.account.export_user", side_effect=OSError("disk full")):
            with pytest.raises(OSError):
                deactivate_account(db_path, user_id)

        assert get_user(db_path, user_id)["deactivated_at"] is None


def test_reactivate_account_clears_the_mark_and_destroys_the_export():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        exports_dir = os.path.join(tmp, "exports")
        init_db(db_path)
        user_id = create_user(db_path, "Rumpel", "es")

        with patch("core.account.config.EXPORTS_DIR", exports_dir):
            path = deactivate_account(db_path, user_id)
            removed = reactivate_account(db_path, user_id)

        assert removed == [path]
        assert not os.path.exists(path)
        assert get_user(db_path, user_id)["deactivated_at"] is None


def test_reactivate_account_finds_the_export_after_a_profile_rename():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        exports_dir = os.path.join(tmp, "exports")
        init_db(db_path)
        user_id = create_user(db_path, "Rumpel", "es")

        with patch("core.account.config.EXPORTS_DIR", exports_dir):
            path = deactivate_account(db_path, user_id)
            update_user_profile(db_path, user_id, name="Mauricio")
            reactivate_account(db_path, user_id)

        assert not os.path.exists(path)


def test_reactivate_account_restores_even_when_the_export_is_already_gone():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        exports_dir = os.path.join(tmp, "exports")
        init_db(db_path)
        user_id = create_user(db_path, "Rumpel", "es")

        with patch("core.account.config.EXPORTS_DIR", exports_dir):
            os.remove(deactivate_account(db_path, user_id))
            removed = reactivate_account(db_path, user_id)

        assert removed == []
        assert get_user(db_path, user_id)["deactivated_at"] is None


def test_reactivate_account_keeps_the_account_deactivated_when_the_export_cannot_be_destroyed():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        exports_dir = os.path.join(tmp, "exports")
        init_db(db_path)
        user_id = create_user(db_path, "Rumpel", "es")

        with patch("core.account.config.EXPORTS_DIR", exports_dir):
            deactivate_account(db_path, user_id)
            with patch("core.account.os.remove", side_effect=OSError("read-only file system")):
                with pytest.raises(OSError):
                    reactivate_account(db_path, user_id)

        assert get_user(db_path, user_id)["deactivated_at"] is not None
