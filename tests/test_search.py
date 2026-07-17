import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch

from core.search import search, web_fetch, web_search, _search_ddg


class TestWebSearch(unittest.TestCase):
    @patch("core.search.DDGS")
    def test_formats_results(self, mock_ddgs_class):
        mock_ddgs_class.return_value.text.return_value = [
            {"title": "Result 1", "body": "Snippet 1", "href": "https://example.com/1"},
            {"title": "Result 2", "body": "Snippet 2", "href": "https://example.com/2"},
        ]
        result = web_search("clima en Panama")
        self.assertIn("Result 1", result)
        self.assertIn("Snippet 1", result)
        self.assertIn("https://example.com/1", result)
        self.assertIn("Result 2", result)


@patch("core.search.DDGS")
def test_search_ddg_normalizes_results(mock_ddgs_class):
    mock_ddgs_class.return_value.text.return_value = [
        {"title": "Result 1", "body": "Snippet 1", "href": "https://example.com/1"},
        {"title": "Result 2", "body": "Snippet 2", "href": "https://example.com/2"},
    ]
    results = _search_ddg("clima en Panama")
    assert results == [
        {"title": "Result 1", "url": "https://example.com/1", "content": "Snippet 1"},
        {"title": "Result 2", "url": "https://example.com/2", "content": "Snippet 2"},
    ]


@patch("core.search.DDGS")
def test_search_uses_configured_provider(mock_ddgs_class):
    mock_ddgs_class.return_value.text.return_value = [
        {"title": "Result 1", "body": "Snippet 1", "href": "https://example.com/1"},
    ]
    results = search("clima en Panama")
    assert results == [
        {"title": "Result 1", "url": "https://example.com/1", "content": "Snippet 1"},
    ]


@patch("core.search.DDGS")
def test_search_returns_empty_when_all_providers_fail(mock_ddgs_class):
    mock_ddgs_class.return_value.text.side_effect = RuntimeError("provider down")
    results = search("clima en Panama")
    assert results == []


@patch("core.search.httpx.get")
def test_web_fetch_extracts_readable_text(mock_get):
    mock_get.return_value.text = (
        "<html><body><h1>Titulo</h1><p>Contenido real</p>"
        "<script>ruido()</script></body></html>"
    )
    result = web_fetch("https://example.com/articulo")
    assert "Titulo" in result
    assert "Contenido real" in result
    assert "ruido" not in result


if __name__ == "__main__":
    unittest.main()