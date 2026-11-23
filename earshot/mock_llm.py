"""Deterministic stand-ins for the LLM, used by tests, CI and the demo (EARSHOT_LLM=mock).

They follow the same output contract as the real prompts, so the whole pipeline (quote checks,
counting, evidence validation, reports) is exercised without a key. They are rules, not intelligence:
mock output is never presented as a finding.
"""
import re

LEXICON = [
    # (type, theme, pattern)
    ("pain", "manual receipt matching", r"receipt matching (still )?breaks|broken receipt matching|matching is hit and miss|fails for small|fixes it by hand"),
    ("pain", "slow month-end close", r"month-end close (still )?takes|close took a full week|days chasing|books can close"),
    ("pain", "accounting sync loses tax codes", r"drops the tax codes|manual fixes for tax codes|manual coding"),
    ("pain", "approvals stuck in email", r"approval flow lives in email|approvals get stuck|approvals got lost"),
    ("pain", "per-seat pricing", r"per-seat pricing|pay for all of them|pay for every employee"),
    ("pain", "missing receipts", r"missing receipts|forgets to upload receipts"),
    ("pain", "mobile app crashes or is slow", r"crashes every time|slow to open"),
    ("pain", "slow support", r"support is slow|waited four days"),
    ("praise", "fast receipt capture", r"takes two seconds|love how fast"),
    ("praise", "approvals from slack", r"approve from slack|approval flow is the best"),
    ("praise", "responsive support", r"support answered in ten minutes"),
    ("praise", "reliable app", r"never crashed"),
    ("praise", "accurate accounting sync", r"best accounting sync|right tax codes every time"),
    ("praise", "fast setup", r"setup took one afternoon"),
    ("objection", "onboarding another tool", r"hesitant to add another tool|training forty people"),
    ("objection", "migrating history", r"worried about migrating|lose the audit trail"),
    ("objection", "long setup", r"setup took us six weeks|built for companies much bigger"),
    ("switch_trigger", "price increase", r"raised prices|after the price increase|enterprise prices"),
    ("switch_trigger", "team outgrew spreadsheets", r"hit thirty employees|spreadsheet broke"),
    ("switch_trigger", "audit finding", r"auditor flagged"),
    ("switch_trigger", "slow close", r"left northbook because"),
    ("feature_request", "per diem support", r"per diem"),
    ("feature_request", "custom csv export", r"csv export with custom columns"),
    ("job", "close the books faster", r"make the books close faster|card, receipt, approval, done"),
]
COMPETITORS = ["Northbook", "Quillsum"]


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _profile(ctx: dict) -> dict:
    text = ctx.get("text", "")
    if "Ledgerly" in text:
        return {"company": "Ledgerly", "one_liner": "Expense management for small teams: cards, receipts and approvals in one place.",
                "category": "expense management", "audience": "finance leads at teams of 5 to 200",
                "claims": ["AI-powered receipt matching", "enterprise-grade security", "spend in 40 currencies",
                           "beautiful analytics dashboards", "one-click accounting sync"],
                "competitors": [{"name": "Northbook", "why": "cheap cards for small teams"},
                                {"name": "Quillsum", "why": "enterprise expense suite"}],
                "search_terms": ["expense management", "receipt matching"]}
    title = (text.splitlines() or ["Unknown"])[0][:40]
    return {"company": title, "one_liner": "Mock profile.", "category": "software", "audience": "teams",
            "claims": [], "competitors": [], "search_terms": []}


def _tag(ctx: dict) -> dict:
    items = []
    for m in ctx.get("batch", []):
        tags = []
        for sent in _sentences(m["text"]):
            low = sent.lower()
            for typ, theme, pat in LEXICON:
                if re.search(pat, low):
                    subj = next((c for c in COMPETITORS if c.lower() in low), None) or m.get("subject_hint") or "category"
                    words = sent.split()
                    tags.append({"type": typ, "theme": theme, "subject": subj, "quote": " ".join(words[:30])})
                    break
        items.append({"id": m["id"], "relevant": bool(tags), "tags": tags[:3]})
    return {"items": items}


PHRASES = {  # demo copy for the fixture themes, so the demo report reads like real output
    "manual receipt matching": ("Receipts that match themselves, even for taxis", "Matching that works for every merchant",
                                "Receipts match automatically, including small merchants with odd card names."),
    "slow month-end close": ("Close the month in hours, not days", "A faster close",
                             "Expenses arrive in the books coded and ready, so the close stops waiting on finance."),
    "per-seat pricing": ("Pay for spenders, not for everyone", "Pricing that fits how teams spend",
                         "Only people who actually spend count, so occasional submitters don't cost a seat."),
    "accounting sync loses tax codes": ("Your ledger, right the first time", "Clean accounting sync",
                                        "Tax codes survive the sync, so nobody fixes exports by hand."),
}


def _synth(ctx: dict) -> dict:
    ev = ctx.get("evidence", [])
    first = lambda typ, theme=None: next((e["id"] for e in ev if e["type"] == typ and (theme is None or e["theme"] == theme)), None)
    ids = lambda *xs: [x for x in xs if x]
    top = list(dict.fromkeys(e["theme"] for e in ev if e["type"] == "pain" and not e.get("weak")))[:3]
    phrase = lambda t, i: PHRASES.get(t, (f"Fix {t}", t.title(), f"Ledgerly removes {t}."))[i]
    out = {
        "positioning": {"for": "finance leads at teams of 20 to 200", "who": "lose days every month to receipts and coding",
                        "category": "expense tool", "unlike": "enterprise suites that need weeks of setup and a consultant",
                        "because": "gets expenses into the books coded and on time",
                        "evidence": ids(first("job"), first("objection", "long setup"), first("pain", "slow month-end close"))},
        "headlines": [{"text": phrase(t, 0), "evidence": ids(first("pain", t))} for t in top],
        "pillars": [{"pillar": phrase(t, 1), "pain": t, "message": phrase(t, 2), "evidence": ids(first("pain", t))} for t in top],
        "objections": [],
        "battlecards": [],
        "gaps": {"claimed_not_heard": ["AI-powered analytics dashboards (one mention, and it says nobody opens them)",
                                       "spend in 40 currencies (no mentions)"],
                 "heard_not_claimed": ["per-seat pricing is the top reason people look elsewhere; the site never mentions pricing",
                                       "accounting sync loses tax codes, while the site promises one-click sync"]},
    }
    answers = {"onboarding another tool": "Occasional submitters only need the mobile app and Slack; no training session.",
               "migrating history": "Import past expenses with their approval trail, so the audit history stays intact.",
               "long setup": "Live in an afternoon, without a consultant."}
    for e in ev:
        if e["type"] == "objection" and e["theme"] in answers and all(o["objection"] != e["theme"] for o in out["objections"]):
            out["objections"].append({"objection": e["theme"].capitalize(), "response": answers[e["theme"]], "evidence": [e["id"]]})
    for c in COMPETITORS:
        cev = [e for e in ev if e.get("subject") == c]
        if cev:
            out["battlecards"].append({"competitor": c,
                                       "they_win": list(dict.fromkeys(e["theme"] for e in cev if e["type"] == "praise"))[:3],
                                       "they_lose": list(dict.fromkeys(e["theme"] for e in cev if e["type"] in ("pain", "objection", "switch_trigger")))[:3],
                                       "evidence": [e["id"] for e in cev][:4]})
    return out


def handle(purpose: str, prompt: str, ctx: dict) -> dict:
    return {"profile": _profile, "tag": _tag, "synthesize": _synth}[purpose](ctx)
