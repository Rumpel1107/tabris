import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import socket
import unittest

import config
from core.search import search, TextBudget, web_fetch, web_search, _search_ddg, _search_tavily
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlsplit


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
        {"title": "Result 1", "url": "https://example.com/1", "content": "Snippet 1", "text": ""},
        {"title": "Result 2", "url": "https://example.com/2", "content": "Snippet 2", "text": ""},
    ]


@pytest.mark.parametrize("with_text, page, expected_text", [
    (False, None, ""),
    (True, "La TRM de hoy es 3.126,08", "La TRM de hoy es 3.126,08"),
])
@patch("core.search.httpx.post")
def test_search_tavily_normalizes_results(mock_post, with_text, page, expected_text):
    mock_post.return_value.json.return_value = {
        "results": [
            {"title": "Result 1", "url": "https://example.com/1", "content": "Snippet 1", "score": 0.9,
             "raw_content": page},
            {"title": "Result 2", "url": "https://example.com/2", "content": "Snippet 2", "score": 0.8,
             "raw_content": page},
        ]
    }
    results = _search_tavily("clima en Panama", with_text=with_text)
    assert results == [
        {"title": "Result 1", "url": "https://example.com/1", "content": "Snippet 1", "text": expected_text},
        {"title": "Result 2", "url": "https://example.com/2", "content": "Snippet 2", "text": expected_text},
    ]
    # asking for page text costs half a second, so it is only asked for when there is room for it
    assert mock_post.call_args.kwargs["json"].get("include_raw_content", False) is with_text


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
    assert results == [{"title": "T", "url": "https://t.co", "content": "from tavily", "text": ""}]


@patch("core.search.DDGS")
def test_search_uses_configured_provider(mock_ddgs_class):
    mock_ddgs_class.return_value.text.return_value = [
        {"title": "Result 1", "body": "Snippet 1", "href": "https://example.com/1"},
    ]
    with patch("core.search.config.SEARCH_PROVIDERS", ["duckduckgo"]):
        results = search("clima en Panama")
    assert results == [
        {"title": "Result 1", "url": "https://example.com/1", "content": "Snippet 1", "text": ""},
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


@pytest.mark.parametrize("url, resolves_to", [
    ("http://192.168.1.1/admin", "192.168.1.1"),
    ("https://invented.example/articulo?id=", "93.184.216.34"),
])
@patch("core.search.httpx.get")
def test_web_fetch_names_the_host_and_never_the_address_it_could_not_read(mock_get, url, resolves_to):
    # the message is a tool result, and every address in a tool result counts as a source: a failed
    # fetch must not be how an invented address becomes one
    mock_get.side_effect = RuntimeError("no route")
    with patch("core.search.socket.getaddrinfo", _resolves_to(resolves_to)):
        result = web_fetch(url)
    assert url not in result
    assert urlsplit(url).hostname in result


def _results(count, text_size=0):
    return [
        {
            "title": f"Result {i}",
            "url": f"https://example.com/{i}",
            "content": f"Snippet {i}",
            "text": "x" * text_size,
        }
        for i in range(count)
    ]


@patch("core.search.search")
def test_web_search_gives_the_page_text_to_the_first_results_only(mock_search):
    mock_search.return_value = _results(5, text_size=100)
    budget = TextBudget(16000)
    with patch("core.search.config.SEARCH_TEXT_RESULTS", 2):
        formatted = web_search("trm hoy", budget=budget)
    assert formatted.count("Page text:") == 2
    assert budget.remaining == 16000 - 200
    # the results beyond the cut still arrive, as the snippets they always were
    assert "Snippet 4" in formatted


@patch("core.search.search")
def test_web_search_keeps_only_the_first_characters_of_a_long_page(mock_search):
    mock_search.return_value = _results(1, text_size=9000)
    budget = TextBudget(16000)
    with patch("core.search.config.SEARCH_TEXT_MAX_CHARS", 4000):
        formatted = web_search("trm hoy", budget=budget)
    assert budget.remaining == 16000 - 4000
    assert "x" * 4000 in formatted
    assert "x" * 4001 not in formatted


@pytest.mark.parametrize("start, pages, left", [
    (16000, 3, 4000),   # room for every page the search is allowed to carry
    (9000, 2, 1000),    # the third no longer fits and is dropped whole, not cut in half
    (0, 0, 0),          # spent: the turn falls back to snippets, which is what it did before
])
@patch("core.search.search")
def test_web_search_stops_at_the_budget_it_was_given(mock_search, start, pages, left):
    mock_search.return_value = _results(3, text_size=4000)
    budget = TextBudget(start)
    with patch("core.search.config.SEARCH_TEXT_MAX_CHARS", 4000), \
         patch("core.search.config.SEARCH_TEXT_RESULTS", 3):
        formatted = web_search("trm hoy", budget=budget)
    assert formatted.count("Page text:") == pages
    assert budget.remaining == left
    assert "Snippet 0" in formatted
    assert mock_search.call_args.kwargs["with_text"] is (start > 0)


if __name__ == "__main__":
    unittest.main()