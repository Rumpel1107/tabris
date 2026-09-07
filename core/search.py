import config
import httpx
import ipaddress
import logging
import socket

from ddgs import DDGS
from lxml import html as lxml_html
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


def _search_ddg(query, max_results=5):
    results = DDGS().text(query, max_results=max_results)
    return [
        {"title": r["title"], "url": r["href"], "content": r["body"]}
        for r in results
    ]


def _search_tavily(query, max_results=5):
    response = httpx.post(
        "https://api.tavily.com/search",
        headers={"Authorization": f"Bearer {config.TAVILY_API_KEY}"},
        json={"query": query, "max_results": max_results},
        timeout=config.PROVIDER_TIMEOUT,
    )
    response.raise_for_status()
    results = response.json()["results"]
    return [
        {"title": r["title"], "url": r["url"], "content": r["content"]}
        for r in results
    ]


_ADAPTERS = {
    "tavily": _search_tavily,
    "duckduckgo": _search_ddg,
}


def search(query, max_results=5):
    for name in config.SEARCH_PROVIDERS:
        try:
            return _ADAPTERS[name](query, max_results=max_results)
        except Exception as e:
            logger.warning(f"search provider '{name}' failed ({e}); trying next...")
    return []


def web_search(query, max_results=5):
    results = search(query, max_results=max_results)
    return "\n\n".join(
        f"{r['title']}\n{r['content']}\n{r['url']}" for r in results
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


def web_fetch(url, max_chars=4000):
    try:
        response = _get_following_redirects(url)
    except BlockedURL as e:
        logger.warning(f"web_fetch refused {url} ({e})")
        return f"Refused to fetch {url}: only public web addresses can be read."
    except Exception as e:
        logger.warning(f"web_fetch failed for {url} ({e})")
        return f"Could not fetch {url}."
    tree = lxml_html.fromstring(response.text)
    for bad in tree.xpath("//script | //style"):
        bad.getparent().remove(bad)
    text = tree.text_content()
    text = " ".join(text.split())
    return text[:max_chars]