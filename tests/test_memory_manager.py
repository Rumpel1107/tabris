import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import unittest
from core.db import init_db, create_user, get_facts
from core.memory_manager import update_memory, parse_facts_response
from unittest.mock import patch

class TestParseFactsResponse(unittest.TestCase):
    
    def test_no_changes(self):
        has_changes, new_facts, retire_ids, error = parse_facts_response("HAS_CHANGES: no")
        self.assertFalse(has_changes)
        self.assertEqual(new_facts, [])
        self.assertEqual(retire_ids, [])
        self.assertIsNone(error)
    
    def test_extracts_new_facts_only(self):
        response = "HAS_CHANGES: yes\nNEW_FACTS:\n- Likes short answers\n- Works on TaxL"
        has_changes, new_facts, retire_ids, error = parse_facts_response(response)
        self.assertTrue(has_changes)
        self.assertEqual(new_facts, ["Likes short answers", "Works on TaxL"])
        self.assertEqual(retire_ids, [])
        self.assertIsNone(error)
    
    def test_extracts_retire_ids_only(self):
        response = "HAS_CHANGES: yes\nRETIRE_IDS: 3, 7"
        has_changes, new_facts, retire_ids, error = parse_facts_response(response)
        self.assertTrue(has_changes)
        self.assertEqual(new_facts, [])
        self.assertEqual(retire_ids, [3, 7])
        self.assertIsNone(error)
    
    def test_extracts_both(self):
        response = "HAS_CHANGES: yes\nNEW_FACTS:\n- New fact\nRETIRE_IDS: 5"
        has_changes, new_facts, retire_ids, error = parse_facts_response(response)
        self.assertTrue(has_changes)
        self.assertEqual(new_facts, ["New fact"])
        self.assertEqual(retire_ids, [5])
        self.assertIsNone(error)
    
    def test_yes_but_nothing_proposed_is_error(self):
        has_changes, new_facts, retire_ids, error = parse_facts_response("HAS_CHANGES: yes")
        self.assertFalse(has_changes)
        self.assertIsNotNone(error)

class TestUpdateMemory(unittest.TestCase):
    
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        init_db(self.db_path)
        self.user_id = create_user(self.db_path, "Rumpel", "es")
    
    def tearDown(self):
        self.tmp.cleanup()
    
    @patch("builtins.input", return_value="si")
    @patch("core.providers.chat")
    def test_saves_confirmed_facts(self, mock_chat, mock_input):
        mock_chat.return_value = "HAS_CHANGES: yes\nNEW_FACTS:\n- Likes short answers\n- Works on TaxL"
        update_memory([], self.db_path, self.user_id)
        contents = [f["content"] for f in get_facts(self.db_path, self.user_id)]
        self.assertIn("Likes short answers", contents)
        self.assertIn("Works on TaxL", contents)
    
    @patch("builtins.input", return_value="no")
    @patch("core.providers.chat")
    def test_rejected_facts_not_saved(self, mock_chat, mock_input):
        mock_chat.return_value = "HAS_CHANGES: yes\nNEW_FACTS:\n- Should not be saved"
        update_memory([], self.db_path, self.user_id)
        contents = [f["content"] for f in get_facts(self.db_path, self.user_id)]
        self.assertNotIn("Should not be saved", contents)
    
    @patch("builtins.input")
    @patch("core.providers.chat")
    def test_no_changes_saves_nothing(self, mock_chat, mock_input):
        mock_chat.return_value = "HAS_CHANGES: no"
        update_memory([], self.db_path, self.user_id)
        self.assertEqual(get_facts(self.db_path, self.user_id), [])
        mock_input.assert_not_called()
    
    @patch("builtins.input")
    @patch("core.providers.chat", side_effect=Exception("connection refused"))
    def test_connection_error_handled(self, mock_chat, mock_input):
        update_memory([], self.db_path, self.user_id)
        self.assertEqual(get_facts(self.db_path, self.user_id), [])
        mock_input.assert_not_called()
    
    @patch("builtins.input")
    @patch("core.providers.chat")
    def test_malformed_response_not_saved(self, mock_chat, mock_input):
        mock_chat.return_value = "HAS_CHANGES: yes"
        update_memory([], self.db_path, self.user_id)
        self.assertEqual(get_facts(self.db_path, self.user_id), [])
        mock_input.assert_not_called()
    
    @patch("builtins.input", return_value="si")
    @patch("core.providers.chat")
    def test_retires_confirmed_ids(self, mock_chat, mock_input):
        from core.db import save_fact, get_facts
        save_fact(self.db_path, self.user_id, "Hecho a retirar")
        facts_before = get_facts(self.db_path, self.user_id)
        fact_id = facts_before[0]["id"]
        
        mock_chat.return_value = f"HAS_CHANGES: yes\nRETIRE_IDS: {fact_id}"
        update_memory([], self.db_path, self.user_id)
        
        facts_after = get_facts(self.db_path, self.user_id)
        self.assertEqual(facts_after, [])
    
    @patch("builtins.input")
    @patch("core.providers.chat")
    def test_watermark_limits_conversation_sent(self, mock_chat, mock_input):
        mock_chat.return_value = "HAS_CHANGES: no"
        history = [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "mensaje viejo"},
            {"role": "assistant", "content": "respuesta vieja"},
            {"role": "user", "content": "mensaje nuevo"},
            {"role": "assistant", "content": "respuesta nueva"},
        ]
        update_memory(history, self.db_path, self.user_id, watermark=3)
        
        prompt_sent = mock_chat.call_args[0][1][0]["content"]
        self.assertNotIn("mensaje viejo", prompt_sent)
        self.assertIn("mensaje nuevo", prompt_sent)


if __name__ == "__main__":
    unittest.main()