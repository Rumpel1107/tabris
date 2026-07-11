import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch

from core.search import web_search


class TestWebSearch(unittest.TestCase):
    @patch("core.search.DDGS")
    def test_formats_results(self, mock_ddgs_class):
        mock_ddgs_class.return_value.text.return_value = [
            {"title": "Result 1", "body": "Snippet 1", "href": "https://example.com/1"},
            {"title": "Result 2", "body": "Snippet 2", "href": "https://example.com/2"},
        ]
        result = web_search("clima en Bogota")
        self.assertIn("Result 1", result)
        self.assertIn("Snippet 1", result)
        self.assertIn("https://example.com/1", result)
        self.assertIn("Result 2", result)


if __name__ == "__main__":
    unittest.main()