import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import socket
import unittest

import config
from core.search import search, web_fetch, web_search, _search_ddg, _search_tavily
from types import SimpleNamespace
from unittest.mock import patch


class TestWebSearch(unittest.TestCase):
    @patch("core.search.DDGS")
    def test_formats_results(self, mock_ddgs_class):
        mock_ddgs_class.return_value.text.return_value = [
            {"title": "Result 1", "body": "Snippet 1", "href": "https://example.com/1"},
            {"title": "Result 2", "body": "Snippet 2", "href": "https://example.com/2"},
        ]
        with patch("core.search.config.SEARCH_PROVIDERS", ["duckduckgo"]):
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


@patch("core.search.httpx.post")
def test_search_tavily_normalizes_results(mock_post):
    mock_post.return_value.json.return_value = {
        "results": [
            {"title": "Result 1", "url": "https://example.com/1", "content": "Snippet 1", "score": 0.9},
            {"title": "Result 2", "url": "https://example.com/2", "content": "Snippet 2", "score": 0.8},
        ]
    }
    results = _search_tavily("clima en Panama")
    assert results == [
        {"title": "Result 1", "url": "https://example.com/1", "content": "Snippet 1"},
        {"title": "Result 2", "url": "https://example.com/2", "content": "Snippet 2"},
    ]


@patch("core.search.DDGS")
@patch("core.search.httpx.post")
def test_search_uses_tavily_when_configured_first(mock_post, mock_ddgs_class):
    mock_post.return_value.json.return_value = {
        "results": [{"title": "T", "url": "https://t.co", "content": "from tavily", "score": 0.9}]
    }
    mock_ddgs_class.return_value.text.return_value = [
        {"title": "D", "body": "from ddg", "href": "https://d.co"}
    ]
    with patch("core.search.config.SEARCH_PROVIDERS", ["tavily", "duckduckgo"]):
        results = search("clima en Panama")
    assert results == [{"title": "T", "url": "https://t.co", "content": "from tavily"}]


@patch("core.search.DDGS")
def test_search_uses_configured_provider(mock_ddgs_class):
    mock_ddgs_class.return_value.text.return_value = [
        {"title": "Result 1", "body": "Snippet 1", "href": "https://example.com/1"},
    ]
    with patch("core.search.config.SEARCH_PROVIDERS", ["duckduckgo"]):
        results = search("clima en Panama")
    assert results == [
        {"title": "Result 1", "url": "https://example.com/1", "content": "Snippet 1"},
    ]


@patch("core.search.DDGS")
def test_search_returns_empty_when_all_providers_fail(mock_ddgs_class):
    mock_ddgs_class.return_value.text.side_effect = RuntimeError("provider down")
    with patch("core.search.config.SEARCH_PROVIDERS", ["duckduckgo"]):
        results = search("clima en Panama")
    assert results == []


def _page(html, status_code=200, location=None):
    """A response shaped like the one httpx returns, redirect or not."""
    return SimpleNamespace(
        text=html,
        status_code=status_code,
        is_redirect=location is not None,
        headers={"location": location} if location else {},
        raise_for_status=lambda: None,
    )


def _resolves_to(ip):
    """Stand in for DNS: whatever host is asked for, it answers with this address."""
    return lambda host, port, *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 0))]


@patch("core.search.httpx.get")
def test_web_fetch_extracts_readable_text(mock_get):
    mock_get.return_value = _page(
        "<html><body><h1>Titulo</h1><p>Contenido real</p>"
        "<script>ruido()</script></body></html>"
    )
    with patch("core.search.socket.getaddrinfo", _resolves_to("93.184.216.34")):
        result = web_fetch("https://example.com/articulo")
    assert "Titulo" in result
    assert "Contenido real" in result
    assert "ruido" not in result


@pytest.mark.parametrize("url", [
    "http://127.0.0.1/admin",
    "http://localhost:8080/",
    "http://169.254.169.254/latest/meta-data/",
    "http://192.168.1.1/",
    "http://10.0.0.5/status",
    "http://[::1]/",
    "file:///etc/passwd",
    "ftp://example.com/x",
])
@patch("core.search.httpx.get")
def test_web_fetch_refuses_anything_but_a_public_http_address(mock_get, url):
    result = web_fetch(url)
    mock_get.assert_not_called()
    assert "Refused" in result


@patch("core.search.httpx.get")
def test_web_fetch_follows_a_redirect_to_a_public_address(mock_get):
    mock_get.side_effect = [
        _page("", status_code=302, location="https://example.com/final"),
        _page("<html><body><p>Contenido final</p></body></html>"),
    ]
    with patch("core.search.socket.getaddrinfo", _resolves_to("93.184.216.34")):
        result = web_fetch("https://example.com/articulo")
    assert "Contenido final" in result
    assert mock_get.call_count == 2


@patch("core.search.httpx.get")
def test_web_fetch_refuses_a_redirect_into_the_private_network(mock_get):
    mock_get.return_value = _page("", status_code=302, location="http://192.168.1.1/admin")
    with patch("core.search.socket.getaddrinfo", _resolves_to("93.184.216.34")):
        result = web_fetch("https://example.com/articulo")
    assert "Refused" in result
    assert mock_get.call_count == 1


@patch("core.search.httpx.get")
def test_web_fetch_gives_up_on_a_redirect_loop(mock_get):
    mock_get.return_value = _page("", status_code=302, location="https://example.com/again")
    with patch("core.search.socket.getaddrinfo", _resolves_to("93.184.216.34")):
        result = web_fetch("https://example.com/articulo")
    assert "Could not fetch" in result
    assert mock_get.call_count == config.WEB_FETCH_MAX_REDIRECTS


@patch("core.search.httpx.get")
def test_web_fetch_refuses_a_host_that_resolves_to_both_public_and_private(mock_get):
    def both(host, port, *args, **kwargs):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0)),
        ]

    with patch("core.search.socket.getaddrinfo", both):
        result = web_fetch("http://rebinding.example/")
    mock_get.assert_not_called()
    assert "Refused" in result


if __name__ == "__main__":
    unittest.main()