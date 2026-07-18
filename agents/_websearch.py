import re
import requests


def duckduckgo_links(query, max_results=3):
    """Fetch a few real result links from DuckDuckGo's HTML endpoint (no API key
    needed). Returns a list of (title, url) tuples, or an empty list if anything
    goes wrong — callers should always have a fallback (e.g. a plain search-query
    link), since this depends on DuckDuckGo's markup staying stable and the
    machine having internet access."""
    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8,
        )
        resp.raise_for_status()
    except Exception:
        return []

    # DuckDuckGo's lite HTML markup wraps each result link like:
    # <a rel="nofollow" class="result__a" href="...">Title</a>
    pattern = re.compile(
        r'<a rel="nofollow" class="result__a" href="(.*?)">(.*?)</a>', re.DOTALL
    )
    matches = pattern.findall(resp.text)

    links = []
    for href, title in matches[:max_results]:
        clean_title = re.sub(r"<.*?>", "", title).strip()
        if href and clean_title:
            links.append((clean_title, href))
    return links


def fallback_search_link(query):
    """A plain search-query link that always works, used when duckduckgo_links()
    returns nothing (network hiccup, markup change, etc.)."""
    from urllib.parse import quote_plus
    return f"https://www.google.com/search?q={quote_plus(query)}"
