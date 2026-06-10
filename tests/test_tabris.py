import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from memory_manager import parse_memory_update, update_memory, replace_section
from tabris import route_message
from config import CODE_MODEL, GENERAL_MODEL
from unittest.mock import patch, MagicMock, mock_open


class TestParseMemoryUpdate(unittest.TestCase):

    def test_no_changes(self):
        response = "HAS_CHANGES: no"
        has_changes, section, content = parse_memory_update(response)
        self.assertFalse(has_changes)
        self.assertIsNone(section)
        self.assertIsNone(content)

    def test_with_changes(self):
        response = "HAS_CHANGES: yes\nSECTION: ### Roadmap\nCONTENT:\nnew content here"
        has_changes, section, content = parse_memory_update(response)
        self.assertTrue(has_changes)
        self.assertEqual(section, "### Roadmap")
        self.assertIn("new content here", content)

    def test_missing_section(self):
        response = "HAS_CHANGES: yes\nCONTENT:\nsome content"
        has_changes, section, content = parse_memory_update(response)
        self.assertTrue(has_changes)
        self.assertIsNone(section)
        self.assertIn("some content", content)


class TestUpdateMemory(unittest.TestCase):

    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch("ollama.chat")
    def test_file_not_found(self, mock_chat, mock_open):
        update_memory([], memory_path="memory.md")
        mock_chat.assert_not_called()
        
    @patch("builtins.open", mock_open(read_data="# memoria falsa"))
    @patch("ollama.chat")
    def test_no_changes(self, mock_chat):
        mock_chat.return_value.message.content = "HAS_CHANGES: no"
        update_memory([], memory_path="memory.md")
        mock_chat.assert_called_once()
    
    @patch("builtins.open", mock_open(read_data="### Roadmap\nold content"))
    @patch("builtins.input", return_value="si")
    @patch("ollama.chat")
    def test_changes_confirmed(self, mock_chat, mock_input,):
        mock_chat.return_value.message.content = "HAS_CHANGES: yes\nSECTION: ### Roadmap\nCONTENT:\nnew content"
        update_memory([], memory_path="memory.md")
        mock_input.assert_called_once()


class TestReplaceSection(unittest.TestCase):

    def test_basic_replacement(self):
        content = "# Title\n\n### Roadmap\nold content\n\n## Other\nother content"
        result = replace_section(content, "### Roadmap", "new content")
        self.assertIn("new content", result)
        self.assertNotIn("old content", result)

    def test_preserves_other_sections(self):
        content = "# Title\n\n### Roadmap\nold content\n\n## Other\nother content"
        result = replace_section(content, "### Roadmap", "new content")
        self.assertIn("## Other", result)
        self.assertIn("other content", result)
        
    def test_handles_internal_subheadings(self):
        content = "# Title\n\n### Roadmap\nold content\n#### Phase 1\nstep 1\n\n## Other\nother"
        result = replace_section(content, "### Roadmap", "new content\n#### Phase 1\nnew step")
        self.assertIn("new content", result)
        self.assertNotIn("old content", result)
        self.assertNotIn("step 1", result)
        self.assertIn("## Other", result)


class TestRouteMessage(unittest.TestCase):

    def test_routes_code_keyword_english(self):
        self.assertEqual(route_message("I have a bug in my code"), CODE_MODEL)

    def test_routes_code_keyword_spanish(self):
        self.assertEqual(route_message("tengo un error en mi función"), CODE_MODEL)

    def test_routes_general_message(self):
        self.assertEqual(route_message("what is machine learning?"), GENERAL_MODEL)


if __name__ == "__main__":
    unittest.main()