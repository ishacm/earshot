"""Step 2: collect public mentions of the product, its competitors and the category."""
from earshot.config import CONFIG
from earshot.privacy import scrub
from earshot.sources import appstore, csvfile, hn, reddit

C = CONFIG["collect"]


def queries(profile: dict) -> list[tuple[str, str]]:
    """(query, subject) pairs: the product, each competitor, and the category terms."""
    q = [(profile["company"], "self")]
    q += [(c["name"], c["name"]) for c in profile.get("competitors", [])]
    q += [(t, "category") for t in profile.get("search_terms", [])[:3]]
    seen, out = set(), []
    for term, subj in q:
        if term and term.lower() not in seen:
            seen.add(term.lower())
            out.append((term, subj))
    return out


def run(profile: dict, csv_paths: list[str] | None = None, fixtures: list[dict] | None = None) -> dict:
    """Returns {"mentions": [...], "sources": {name: status}}. fixtures replaces live sources (demo/tests)."""
    status, raw = {}, []
    if fixtures is not None:
        raw = list(fixtures)
        status["fixtures"] = f"{len(raw)} mentions (demo data)"
    else:
        for term, subj in queries(profile):
            if C["hn"]["enabled"]:
                got = hn.fetch(term, C["max_per_source"], C["hn"]["tags"], C["cache_hours"])
                status[f"hackernews:{term}"] = "unavailable" if got is None else len(got)
                raw += [dict(m, subject_hint=subj) for m in got or []]
            if C["reddit"]["enabled"] and reddit.enabled():
                got = reddit.fetch(term, C["max_per_source"])
                status[f"reddit:{term}"] = "unavailable" if got is None else len(got)
                raw += [dict(m, subject_hint=subj) for m in got or []]
            if C["appstore"]["enabled"] and subj != "category":
                got = appstore.fetch(term, C["appstore"]["country"], C["appstore"]["pages"], C["cache_hours"])
                status[f"appstore:{term}"] = "unavailable" if got is None else len(got)
                raw += [dict(m, subject_hint=subj) for m in got or []]
        if not reddit.enabled():
            status["reddit"] = "skipped (no REDDIT_CLIENT_ID/SECRET)"
    for p in csv_paths or []:
        got = csvfile.load(p, profile.get("company", ""))
        status[f"csv:{p}"] = len(got)
        raw += [dict(m, subject_hint="self") for m in got]

    seen, mentions = set(), []
    for m in raw:
        text = scrub(m["text"]).strip()
        key = text[:120].lower()
        if len(text) < C["min_chars"] or key in seen or m["id"] in seen:
            continue
        seen.update({key, m["id"]})
        mentions.append({**m, "text": text[:2000]})
    dropped = max(0, len(mentions) - C["max_mentions"])
    mentions = mentions[:C["max_mentions"]]
    return {"mentions": mentions, "sources": status, "capped": dropped}
