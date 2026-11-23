"""Reddit posts via the official API with app-only OAuth. Skipped unless you set your own credentials."""
import os
import urllib.parse

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
SEARCH = "https://oauth.reddit.com/search?q={q}&limit={n}&sort=relevance&t=year&type=link"
UA = "Earshot/0.1 (research tool; by u/your_username)"


def enabled() -> bool:
    return bool(os.environ.get("REDDIT_CLIENT_ID") and os.environ.get("REDDIT_CLIENT_SECRET"))


def parse(data: dict, query: str) -> list[dict]:
    out = []
    for c in ((data or {}).get("data") or {}).get("children", []):
        d = c.get("data") or {}
        text = f"{d.get('title', '')}. {d.get('selftext', '')}".strip(". ")
        if not text:
            continue
        out.append({"id": f"rd-{d.get('id')}", "source": "reddit",
                    "url": "https://www.reddit.com" + (d.get("permalink") or ""),
                    "date": "", "text": text, "query": query})
    return out


def fetch(query: str, n: int = 60) -> list[dict] | None:
    if not enabled():
        return None
    import httpx
    try:
        tok = httpx.post(TOKEN_URL, auth=(os.environ["REDDIT_CLIENT_ID"], os.environ["REDDIT_CLIENT_SECRET"]),
                         data={"grant_type": "client_credentials"}, headers={"User-Agent": UA}, timeout=20)
        tok.raise_for_status()
        r = httpx.get(SEARCH.format(q=urllib.parse.quote(f'"{query}"'), n=min(n, 100)),
                      headers={"Authorization": f"bearer {tok.json()['access_token']}", "User-Agent": UA}, timeout=20)
        r.raise_for_status()
    except Exception:
        return None
    return parse(r.json(), query)
