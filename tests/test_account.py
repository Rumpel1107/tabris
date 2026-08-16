import json
import os
import pytest
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.account import export_user
from core.db import create_user_with_channel, deactivate_fact, deactivate_message, init_db, save_fact, save_message


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
