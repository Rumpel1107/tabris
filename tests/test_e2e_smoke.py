import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import unittest
from unittest.mock import patch

import config
import main
from core.strings import msg
from core.db import find_user_by_name, get_messages


class TestChatE2ESmoke(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "smoke.db")

    def tearDown(self):
        self.tmp.cleanup()

    @patch("main.providers.chat")
    @patch("builtins.input")
    def test_conversation_persists_to_db(self, mock_input, mock_chat):
        mock_input.side_effect = ["Hola", msg("exit_command")]
        mock_chat.side_effect = ["Reply from Tabris", "HAS_NEW_FACTS: no"]

        with patch.object(config, "DB_PATH", self.db_path), \
            patch.object(config, "USER_NAME", "TestUser"):
            main.chat()

        user = find_user_by_name(self.db_path, "TestUser")
        self.assertIsNotNone(user)

        contents = [m["content"] for m in get_messages(self.db_path, user["id"])]
        self.assertIn("Hola", contents)
        self.assertIn("Reply from Tabris", contents)