import config
import httpx
import ipaddress
import logging
import socket

from ddgs import DDGS
from lxml import html as lxml_html
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class TextBudget:
    """How much page text one turn may still carry. Shared by every search of that turn."""

    def __init__(self, remaining: int):
        self.remaining = remaining

    def spend(self, size: int) -> bool:
        """Take `size` from the budget, or leave it untouched and answer False when it no longer fits."""
        if size > self.remaining:
            return False
        self.remaining -= size
        return True


def _search_ddg(query, max_results=5, with_text=False):
    # DuckDuckGo returns snippets only, so a turn that falls back here reads no pages
    results = DDGS().text(query, max_results=max_results)
    return [
        {"title": r["title"], "url": r["href"], "content": r["body"], "text": ""}
        for r in results
    ]


def _search_tavily(query, max_results=5, with_text=False):
    payload = {"query": query, "max_results": max_results}
    if with_text:
        # the page text rides along with the same call: no extra credit, about half a second
        payload["include_raw_content"] = True
    response = httpx.post(
        "https://api.tavily.com/search",
        headers={"Authorization": f"Bearer {config.TAVILY_API_KEY}"},
        json=payload,
        timeout=config.PROVIDER_TIMEOUT,
    )
    response.raise_for_status()
    results = response.json()["results"]
    return [
        {
            "title": r["title"],
            "url": r["url"],
            "content": r["content"],
            "text": (r.get("raw_content") or "") if with_text else "",
        }
        for r in results
    ]


_ADAPTERS = {
    "tavily": _search_tavily,
    "duckduckgo": _search_ddg,
}


def search(query, max_results=5, with_text=False):
    for name in config.SEARCH_PROVIDERS:
        try:
            return _ADAPTERS[name](query, max_results=max_results, with_text=with_text)
        except Exception as e:
            logger.warning(f"search provider '{name}' failed ({e}); trying next...")
    return []


def _with_page_text(result, budget):
    """The result as the model sees it: the snippet always, the page text while the turn can afford it."""
    block = f"{result['title']}\n{result['content']}\n{result['url']}"
    text = result["text"][:config.SEARCH_TEXT_MAX_CHARS]
    if not text or not budget.spend(len(text)):
        return block
    return f"{block}\nPage text:\n{text}"


def web_search(query, max_results=5, budget=None):
    budget = budget or TextBudget(0)
    results = search(query, max_results=max_results, with_text=budget.remaining > 0)
    return "\n\n".join(
        _with_page_text(r, budget) if i < config.SEARCH_TEXT_RESULTS
        else f"{r['title']}\n{r['content']}\n{r['url']}"
        for i, r in enumerate(results)
    )


class BlockedURL(Exception):
    """A URL that must not be requested at all: wrong scheme, or an address inside the network."""


def _is_public_host(host: str) -> bool:
    """True only when every address the host resolves to is routable on the public internet."""
    try:
        # a literal address is the answer already; asking DNS about it only adds a way to be wrong
        return ipaddress.ip_address(host.strip("[]")).is_global
    except ValueError:
        pass
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except socket.gaierror:
        return False
    # every one, not any: a host answering with both a public and a private address is the attack
    return bool(addresses) and all(ipaddress.ip_address(a).is_global for a in addresses)


def _check_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise BlockedURL(f"{url} is not an http(s) address")
    if not _is_public_host(parsed.hostname):
        raise BlockedURL(f"{url} resolves outside the public internet")


def _get_following_redirects(url: str):
    """Walk the redirect chain by hand, so every hop is checked and not only the one the model gave."""
    for _ in range(config.WEB_FETCH_MAX_REDIRECTS):
        _check_url(url)
        response = httpx.get(url, timeout=config.PROVIDER_TIMEOUT, follow_redirects=False)
        if not response.is_redirect:
            response.raise_for_status()
            return response
        url = urljoin(url, response.headers["location"])
    raise RuntimeError(f"more than {config.WEB_FETCH_MAX_REDIRECTS} redirects")


def _named(url: str) -> str:
    """What a failed fetch may repeat back: the host, never the address it was given.

    Its message is a tool result, and every address in a tool result counts as a source — so
    echoing the address would let a fetch that failed turn an invented one into a source.
    """
    return urlparse(url).hostname or "that address"


def web_fetch(url, max_chars=4000):
    try:
        response = _get_following_redirects(url)
    except BlockedURL as e:
        logger.warning(f"web_fetch refused {url} ({e})")
        return f"Refused to fetch {_named(url)}: only public web addresses can be read."
    except Exception as e:
        logger.warning(f"web_fetch failed for {url} ({e})")
        return f"Could not fetch {_named(url)}."
    tree = lxml_html.fromstring(response.text)
    for bad in tree.xpath("//script | //style"):
        bad.getparent().remove(bad)
    text = tree.text_content()
    text = " ".join(text.split())
    return text[:max_chars]