import config
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import unittest

from channels import cli
from core import providers
from core.db import register_user_channel, get_messages
from core.strings import msg
from unittest.mock import patch


class TestChatE2ESmoke(unittest.TestCase):
    
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "smoke.db")
    
    def tearDown(self):
        self.tmp.cleanup()
    
    @patch("core.providers.chat")
    @patch("builtins.input")
    @patch("channels.cli.get_client_key", return_value="test-key-123")
    def test_conversation_persists_to_db(self, mock_key, mock_input, mock_chat):
        mock_input.side_effect = ["Hola", msg("exit_command", "es")]
        mock_chat.side_effect = [
            providers.ChatResponse(content="general", tool_calls=None),
            providers.ChatResponse(content="Reply from Tabris", tool_calls=None),
            providers.ChatResponse(content="exit", tool_calls=None),
            providers.ChatResponse(content="HAS_CHANGES: no", tool_calls=None)
        ]
        
        from core.db import init_db, create_user, register_user_channel
        init_db(self.db_path)
        user_id = create_user(self.db_path, "TestUser", "es")
        register_user_channel(self.db_path, user_id, "cli", "test-key-123")
        
        with patch.object(config, "DB_PATH", self.db_path):
            cli.chat()
        
        contents = [m["content"] for m in get_messages(self.db_path, user_id)]
        self.assertIn("Hola", contents)
        self.assertIn("Reply from Tabris", contents)
    
    @patch("core.providers.chat")
    def test_retire_fact_e2e(self, mock_chat):
        from core.db import init_db, create_user, save_fact, get_facts
        from core.memory_manager import analyze_memory, apply_memory_changes
        
        db_path = os.path.join(self.tmp.name, "retire_smoke.db")
        init_db(db_path)
        user_id = create_user(db_path, "TestUser", "es")
        save_fact(db_path, user_id, "Trabaja en TaxL")
        
        fact_id = get_facts(db_path, user_id)[0]["id"]
        
        mock_chat.return_value = providers.ChatResponse(content=f"HAS_CHANGES: yes\nRETIRE_IDS: {fact_id}", tool_calls=None)
        changes = analyze_memory([], db_path, user_id, language="es")
        apply_memory_changes(db_path, user_id, changes)
        
        self.assertEqual(get_facts(db_path, user_id), [])
        
        prompt_sent = mock_chat.call_args[0][1][0]["content"]
        self.assertIn(f"[{fact_id}]", prompt_sent)


class TestNewUserLanguageE2E(unittest.TestCase):
    
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "newuser_smoke.db")
    
    def tearDown(self):
        self.tmp.cleanup()
    
    @patch("core.providers.chat")
    @patch("builtins.input")
    @patch("channels.cli.get_client_key", return_value="new-user-key")
    def test_new_spanish_user_full_flow(self, mock_key, mock_input, mock_chat):
        mock_input.side_effect = [
            "Hola, como estas",  # first message (triggers language detection)
            "si",                # confirms detected language
            "Carlos",            # name (no link code pasted)
            "Panama",            # city (asked after name)
            "si, correcto",      # confirms the profile read back before saving
            "Cuentame algo",     # first real request, answered normally
            "salir",             # ends the session
        ]
        mock_chat.side_effect = [
            providers.ChatResponse(content="es", tool_calls=None),                   # detect_language
            providers.ChatResponse(content="yes", tool_calls=None),                  # interpret_yes_no confirms language
            providers.ChatResponse(content="Carlos", tool_calls=None),             # extract_name
            providers.ChatResponse(content="yes", tool_calls=None),                  # is_timezone_ambiguous: enough info, no reask
            providers.ChatResponse(content="America/Panama", tool_calls=None),       # resolve_timezone
            providers.ChatResponse(content="Panama", tool_calls=None),               # extract_location
            providers.ChatResponse(content="yes", tool_calls=None),                  # interpret_yes_no confirms the read-back
            providers.ChatResponse(content="general", tool_calls=None),              # route_message for the real request
            providers.ChatResponse(content="Respuesta de Tabris", tool_calls=None),  # model reply
            providers.ChatResponse(content="exit", tool_calls=None),                 # route_message for "salir"
            providers.ChatResponse(content="HAS_CHANGES: no", tool_calls=None),      # memory_manager on exit
        ]
        
        from core.db import init_db, find_user_by_key, get_messages
        init_db(self.db_path)
        
        with patch.object(config, "DB_PATH", self.db_path):
            cli.chat()
        
        user = find_user_by_key(self.db_path, "cli", "new-user-key")
        self.assertEqual(user["name"], "Carlos")
        self.assertEqual(user["language"], "es")
        self.assertEqual(user["location"], "Panama")
        self.assertEqual(user["timezone"], "America/Panama")
        contents = [m["content"] for m in get_messages(self.db_path, user["id"])]
        self.assertIn("Cuentame algo", contents)
        self.assertIn("Respuesta de Tabris", contents)

@patch("channels.cli.memory_manager.analyze_memory")
@patch("core.providers.chat")
@patch("builtins.input")
@patch("channels.cli.get_client_key", return_value="test-key-123")
def test_exit_without_new_turns_skips_distillation(mock_key, mock_input, mock_chat, mock_analyze):
    from core.db import init_db, create_user

    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "exit_smoke.db")
        init_db(db_path)
        user_id = create_user(db_path, "TestUser", "es")
        register_user_channel(db_path, user_id, "cli", "test-key-123")

        mock_input.side_effect = [msg("exit_command", "es")]
        mock_chat.side_effect = [providers.ChatResponse(content="exit", tool_calls=None)]

        with patch.object(config, "DB_PATH", db_path):
            cli.chat()

        mock_analyze.assert_not_called()