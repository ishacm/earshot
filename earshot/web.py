"""HTTP with a small on-disk cache, a clear user agent and no retries against rate limits."""
import hashlib
import html
import json
import re
import time
from pathlib import Path

from earshot import ROOT

CACHE = ROOT / ".cache"
UA = "Earshot/0.1 (+https://github.com/ishacm/earshot; research tool)"


def _cache_path(url: str) -> Path:
    return CACHE / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".json")


def get(url: str, *, as_json: bool = False, cache_hours: float = 24, headers: dict | None = None,
        timeout: float = 20):
    """GET a URL. Returns text / parsed JSON, or None on failure (callers treat None as 'source unavailable')."""
    p = _cache_path(url)
    if p.exists() and time.time() - p.stat().st_mtime < cache_hours * 3600:
        body = json.loads(p.read_text())["body"]
    else:
        import httpx
        try:
            r = httpx.get(url, timeout=timeout, follow_redirects=True, headers={"User-Agent": UA, **(headers or {})})
        except Exception:
            return None
        if r.status_code != 200:
            return None
        body = r.text
        CACHE.mkdir(exist_ok=True)
        p.write_text(json.dumps({"url": url, "body": body}))
    if as_json:
        try:
            return json.loads(body)
        except ValueError:
            return None
    return body


def html_to_text(raw: str, limit: int = 8000) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", raw or "")
    raw = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h[1-6])>", "\n", raw)
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text).strip()
    return text[:limit]
