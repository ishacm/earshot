"""Hacker News comments via the public Algolia API (no key)."""
import html
import re
import urllib.parse

from earshot import web

API = "https://hn.algolia.com/api/v1/search?query={q}&tags={tags}&hitsPerPage={n}"


def parse(data: dict, query: str) -> list[dict]:
    out = []
    for h in (data or {}).get("hits", []):
        raw = h.get("comment_text") or h.get("story_text") or ""
        text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        oid = h.get("objectID")
        out.append({"id": f"hn-{oid}", "source": "hackernews", "url": f"https://news.ycombinator.com/item?id={oid}",
                    "date": (h.get("created_at") or "")[:10], "text": text, "query": query})
    return out


def fetch(query: str, n: int = 60, tags: str = "comment", cache_hours: float = 24) -> list[dict] | None:
    url = API.format(q=urllib.parse.quote(f'"{query}"'), tags=tags, n=min(n, 100))
    data = web.get(url, as_json=True, cache_hours=cache_hours)
    return None if data is None else parse(data, query)
