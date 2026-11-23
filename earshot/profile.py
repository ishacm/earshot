"""Step 1: read the website and work out the company, category, claims and likely competitors."""
from earshot import ROOT, web
from earshot.llm import complete_json

PROMPT = (ROOT / "prompts" / "profile.md").read_text()


def build(url: str, html: str | None = None, overrides: dict | None = None) -> dict:
    raw = html if html is not None else web.get(url, cache_hours=24)
    if not raw:
        raise RuntimeError(f"could not load {url}")
    text = web.html_to_text(raw, 6000)
    prof = complete_json(PROMPT.replace("{url}", url).replace("{text}", text), "profile",
                         context={"url": url, "text": text})
    prof["url"] = url
    prof["competitors_confirmed"] = False
    for k, v in (overrides or {}).items():
        if v:
            prof[k] = v
    if overrides and overrides.get("competitors"):
        prof["competitors_confirmed"] = True
    prof["competitors"] = [c if isinstance(c, dict) else {"name": c, "why": "given by user"}
                           for c in prof.get("competitors", [])][:4]
    return prof
