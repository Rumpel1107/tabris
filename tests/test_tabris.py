import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from memory_manager import replace_section
from tabris import route_message
from config import CODE_MODEL, GENERAL_MODEL


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