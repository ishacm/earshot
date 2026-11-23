"""Apple App Store customer reviews via the public iTunes RSS feed (no key). Only for products with an app."""
import urllib.parse

from earshot import web

LOOKUP = "https://itunes.apple.com/search?term={q}&entity=software&limit=1&country={cc}"
FEED = "https://itunes.apple.com/{cc}/rss/customerreviews/page={page}/id={app}/sortby=mostrecent/json"


def find_app(name: str, country: str = "us", cache_hours: float = 24) -> dict | None:
    data = web.get(LOOKUP.format(q=urllib.parse.quote(name), cc=country), as_json=True, cache_hours=cache_hours)
    res = (data or {}).get("results") or []
    if not res:
        return None
    r = res[0]
    # only accept an exact-ish name match, otherwise we'd collect reviews of a different app
    if name.lower() not in (r.get("trackName") or "").lower():
        return None
    return {"id": r["trackId"], "name": r.get("trackName")}


def parse(data: dict, app_id, query: str) -> list[dict]:
    entries = ((data or {}).get("feed") or {}).get("entry") or []
    if isinstance(entries, dict):
        entries = [entries]
    out = []
    for e in entries:
        if "content" not in e:
            continue  # the first entry can be the app itself
        title = (e.get("title") or {}).get("label", "")
        body = (e.get("content") or {}).get("label", "")
        rid = (e.get("id") or {}).get("label", "")
        out.append({"id": f"as-{rid}", "source": "appstore",
                    "url": f"https://apps.apple.com/app/id{app_id}",
                    "date": ((e.get("updated") or {}).get("label") or "")[:10],
                    "text": f"{title}. {body}".strip(". "), "query": query,
                    "rating": int((e.get("im:rating") or {}).get("label", 0) or 0)})
    return out


def fetch(name: str, country: str = "us", pages: int = 2, cache_hours: float = 24) -> list[dict] | None:
    app = find_app(name, country, cache_hours)
    if not app:
        return []
    out = []
    for page in range(1, pages + 1):
        data = web.get(FEED.format(cc=country, page=page, app=app["id"]), as_json=True, cache_hours=cache_hours)
        if data is None:
            break
        out += parse(data, app["id"], name)
    return out
