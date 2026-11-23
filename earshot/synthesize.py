"""Step 4: count themes, pick the strongest quotes, and turn them into messaging.

Counting is done in code (not by the model), so the numbers are reproducible. The model only writes
messaging on top of numbered evidence, and any item that cites no valid evidence is dropped.
"""
from collections import Counter, defaultdict

from earshot import ROOT
from earshot.config import CONFIG
from earshot.llm import complete_json

PROMPT = (ROOT / "prompts" / "synthesize.md").read_text()
S = CONFIG["synthesize"]


def themes(tags: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for t in tags:
        groups[(t["type"], t["theme"])].append(t)
    out = []
    for (typ, theme), ts in groups.items():
        mentions = {t["mention_id"] for t in ts}
        quotes, seen = [], set()
        for t in sorted(ts, key=lambda t: -len(t["quote"])):
            if t["mention_id"] in seen:
                continue
            seen.add(t["mention_id"])
            quotes.append({k: t[k] for k in ("quote", "url", "source", "date", "subject")})
        out.append({"type": typ, "theme": theme, "mentions": len(mentions),
                    "subjects": dict(Counter(t["subject"] for t in ts)),
                    "sources": dict(Counter(t["source"] for t in ts)),
                    "weak": len(mentions) < S["min_mentions_for_theme"], "quotes": quotes[:S["quotes_per_theme"]]})
    return sorted(out, key=lambda x: (-x["mentions"], x["theme"]))


def evidence(theme_list: list[dict]) -> tuple[list[dict], str]:
    """Strong themes first. Then the best weak theme of each type and subject that has no strong one yet,
    marked as weak, so rare-but-important objections and switching triggers still reach the messaging."""
    strong = [t for t in theme_list if not t["weak"]][:S["top_themes"] * 2]
    covered = {(t["type"], s) for t in strong for s in t["subjects"]}
    extra = []
    priority = {"objection": 0, "switch_trigger": 1, "praise": 2}
    for t in sorted(theme_list, key=lambda t: (priority.get(t["type"], 3), -t["mentions"])):
        if t["weak"] and any((t["type"], s) not in covered for s in t["subjects"]):
            extra.append(t)
            covered |= {(t["type"], s) for s in t["subjects"]}
    ev, lines = [], []
    for th in strong + extra[:S["top_themes"] + 4]:
        for q in th["quotes"]:
            eid = f"E{len(ev) + 1}"
            ev.append({"id": eid, "theme": th["theme"], "type": th["type"], "weak": th["weak"], **q})
            flag = " · WEAK SIGNAL" if th["weak"] else ""
            lines.append(f'{eid} [{th["type"]} · {th["theme"]} · {th["mentions"]} mentions{flag} · about: {q["subject"]}] "{q["quote"]}"')
    return ev, "\n".join(lines)


def _valid(item: dict, ids: set) -> bool:
    item["evidence"] = [e for e in item.get("evidence", []) if e in ids]
    return bool(item["evidence"])


def run(profile: dict, tags: list[dict]) -> dict:
    th = themes(tags)
    ev, block = evidence(th)
    if not ev:
        return {"themes": th, "evidence": [], "messaging": None, "dropped_uncited": 0,
                "note": "Not enough repeated evidence to write messaging. Add sources or a CSV export."}
    prompt = (PROMPT.replace("{company}", profile.get("company", "")).replace("{one_liner}", profile.get("one_liner", ""))
              .replace("{category}", profile.get("category", "")).replace("{audience}", profile.get("audience", ""))
              .replace("{claims}", "; ".join(profile.get("claims", [])) or "none found").replace("{evidence}", block))
    msg = complete_json(prompt, "synthesize", context={"profile": profile, "evidence": ev, "themes": th},
                        max_tokens=2500)
    ids, dropped = {e["id"] for e in ev}, 0
    for key in ("headlines", "pillars", "objections", "battlecards"):
        keep = [x for x in msg.get(key, []) if isinstance(x, dict) and _valid(x, ids)]
        dropped += len(msg.get(key, [])) - len(keep)
        msg[key] = keep
    pos = msg.get("positioning") or {}
    if pos and not _valid(pos, ids):
        msg["positioning"], dropped = None, dropped + 1
    msg.setdefault("gaps", {"claimed_not_heard": [], "heard_not_claimed": []})
    return {"themes": th, "evidence": ev, "messaging": msg, "dropped_uncited": dropped}
