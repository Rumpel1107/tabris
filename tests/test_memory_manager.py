import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import unittest
from core.db import init_db, create_user, get_facts
from core.memory_manager import update_memory, parse_facts_response
from unittest.mock import patch


class TestParseFactsResponse(unittest.TestCase):
    
    def test_no_new_facts(self):
        has_facts, facts, error = parse_facts_response("HAS_NEW_FACTS: no")
        self.assertFalse(has_facts)
        self.assertEqual(facts, [])
        self.assertIsNone(error)
    
    def test_extracts_multiple_facts(self):
        response = "HAS_NEW_FACTS: yes\nFACTS:\n- Likes short answers\n- Works on TaxL"
        has_facts, facts, error = parse_facts_response(response)
        self.assertTrue(has_facts)
        self.assertEqual(facts, ["Likes short answers", "Works on TaxL"])
        self.assertIsNone(error)
    
    def test_strips_bullets_and_whitespace(self):
        response = "HAS_NEW_FACTS: yes\nFACTS:\n-   Lives in Colombia  \n-Uses VS Code"
        has_facts, facts, error = parse_facts_response(response)
        self.assertEqual(facts, ["Lives in Colombia", "Uses VS Code"])
    
    def test_yes_but_no_facts_is_error(self):
        response = "HAS_NEW_FACTS: yes\nFACTS:"
        has_facts, facts, error = parse_facts_response(response)
        self.assertFalse(has_facts)
        self.assertEqual(facts, [])
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
        mock_chat.return_value = "HAS_NEW_FACTS: yes\nFACTS:\n- Likes short answers\n- Works on TaxL"
        update_memory([], self.db_path, self.user_id)
        contents = [f["content"] for f in get_facts(self.db_path, self.user_id)]
        self.assertIn("Likes short answers", contents)
        self.assertIn("Works on TaxL", contents)
    
    @patch("builtins.input", return_value="no")
    @patch("core.providers.chat")
    def test_rejected_facts_not_saved(self, mock_chat, mock_input):
        mock_chat.return_value = "HAS_NEW_FACTS: yes\nFACTS:\n- Should not be saved"
        update_memory([], self.db_path, self.user_id)
        contents = [f["content"] for f in get_facts(self.db_path, self.user_id)]
        self.assertNotIn("Should not be saved", contents)
    
    @patch("builtins.input")
    @patch("core.providers.chat")
    def test_no_new_facts_saves_nothing(self, mock_chat, mock_input):
        mock_chat.return_value = "HAS_NEW_FACTS: no"
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
        mock_chat.return_value = "HAS_NEW_FACTS: yes\nFACTS:"
        update_memory([], self.db_path, self.user_id)
        self.assertEqual(get_facts(self.db_path, self.user_id), [])
        mock_input.assert_not_called()


if __name__ == "__main__":
    unittest.main()