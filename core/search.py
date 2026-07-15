import config
import httpx
import logging

from ddgs import DDGS
from lxml import html as lxml_html

logger = logging.getLogger(__name__)


def _search_ddg(query, max_results=5):
    results = DDGS().text(query, max_results=max_results)
    return [
        {"title": r["title"], "url": r["href"], "content": r["body"]}
        for r in results
    ]


_ADAPTERS = {
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


def web_fetch(url, max_chars=4000):
    try:
        response = httpx.get(url, timeout=config.PROVIDER_TIMEOUT, follow_redirects=True)
        response.raise_for_status()
    except Exception as e:
        logger.warning(f"web_fetch failed for {url} ({e})")
        return f"Could not fetch {url}."
    tree = lxml_html.fromstring(response.text)
    for bad in tree.xpath("//script | //style"):
        bad.getparent().remove(bad)
    text = tree.text_content()
    text = " ".join(text.split())
    return text[:max_chars]