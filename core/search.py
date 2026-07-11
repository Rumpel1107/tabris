from ddgs import DDGS


def web_search(query, max_results=5):
    results = DDGS().text(query, max_results=max_results)
    return "\n\n".join(
        f"{r['title']}\n{r['body']}\n{r['href']}" for r in results
    )