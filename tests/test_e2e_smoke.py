import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import unittest
from unittest.mock import patch

import config
import main
from core.strings import msg
from core.db import register_user_channel, get_messages


class TestChatE2ESmoke(unittest.TestCase):
    
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "smoke.db")
    
    def tearDown(self):
        self.tmp.cleanup()
    
    @patch("main.providers.chat")
    @patch("builtins.input")
    @patch("main.get_client_key", return_value="test-key-123")
    def test_conversation_persists_to_db(self, mock_key, mock_input, mock_chat):
        mock_input.side_effect = ["Hola", msg("exit_command")]
        mock_chat.side_effect = ["general", "Reply from Tabris", "exit", "HAS_CHANGES: no"]
        
        from core.db import init_db, create_user, register_user_channel
        init_db(self.db_path)
        user_id = create_user(self.db_path, "TestUser", "es")
        register_user_channel(self.db_path, user_id, "cli", "test-key-123")
        
        with patch.object(config, "DB_PATH", self.db_path):
            main.chat()
        
        contents = [m["content"] for m in get_messages(self.db_path, user_id)]
        self.assertIn("Hola", contents)
        self.assertIn("Reply from Tabris", contents)
    
    @patch("builtins.input", return_value="si")
    @patch("core.providers.chat")
    def test_retire_fact_e2e(self, mock_chat, mock_input):
        from core.db import init_db, create_user, save_fact, get_facts
        from core.memory_manager import update_memory
        
        db_path = os.path.join(self.tmp.name, "retire_smoke.db")
        init_db(db_path)
        user_id = create_user(db_path, "TestUser", "es")
        save_fact(db_path, user_id, "Trabaja en TaxL")
        
        facts = get_facts(db_path, user_id)
        fact_id = facts[0]["id"]
        
        mock_chat.return_value = f"HAS_CHANGES: yes\nRETIRE_IDS: {fact_id}"
        update_memory([], db_path, user_id)
        
        self.assertEqual(get_facts(db_path, user_id), [])
        
        prompt_sent = mock_chat.call_args[0][1][0]["content"]
        self.assertIn(f"[{fact_id}]", prompt_sent)

class TestNewUserLanguageE2E(unittest.TestCase):
    
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "newuser_smoke.db")
    
    def tearDown(self):
        self.tmp.cleanup()
    
    @patch("main.providers.chat")
    @patch("builtins.input")
    @patch("main.get_client_key", return_value="new-user-key")
    def test_new_spanish_user_full_flow(self, mock_key, mock_input, mock_chat):
        mock_input.side_effect = [
            "Mauricio",          # onboard_user: name
            "Hola, como estas",  # first message (triggers language detection)
            "si",                # confirms detected language
            "salir",             # ends the session
        ]
        mock_chat.side_effect = [
            "Mauricio",             # extract_name during onboarding
            "es",                   # detect_language detects Spanish
            "general",              # route_message for the first message
            "Respuesta de Tabris",  # model reply
            "exit",                 # route_message for "salir"
            "HAS_CHANGES: no",      # memory_manager on exit
        ]
        
        from core.db import init_db, find_user_by_key
        init_db(self.db_path)
        
        with patch.object(config, "DB_PATH", self.db_path):
            main.chat()
        
        user = find_user_by_key(self.db_path, "cli", "new-user-key")
        self.assertEqual(user["language"], "es")