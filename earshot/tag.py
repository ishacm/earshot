"""Step 3: tag each mention with pains, jobs, objections, praise and switching triggers.

The rule that makes this trustworthy: every quote must be an exact substring of the mention it came
from. Quotes the model paraphrased or invented are dropped and counted, never shown.
"""
import json
import re

from earshot import ROOT
from earshot.config import CONFIG
from earshot.llm import complete_json

PROMPT = (ROOT / "prompts" / "tag.md").read_text()
TYPES = CONFIG["tag"]["types"]


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("’", "'").replace("“", '"').replace("”", '"')).strip().lower()


def verify_quote(quote: str, text: str) -> bool:
    q = _norm(quote)
    return len(q.split()) >= 3 and q in _norm(text)


def canon_theme(theme: str) -> str:
    t = re.sub(r"[^a-z0-9 &/+-]", "", (theme or "").lower()).strip()
    return re.sub(r"\s+", " ", t)[:48]


def run(profile: dict, mentions: list[dict]) -> dict:
    by_id = {m["id"]: m for m in mentions}
    competitors = [c["name"] for c in profile.get("competitors", [])]
    tags, themes, stats = [], [], {"mentions": len(mentions), "relevant": 0, "tags": 0,
                                   "quotes_rejected": 0, "bad_type": 0}
    bs = CONFIG["tag"]["batch_size"]
    for i in range(0, len(mentions), bs):
        batch = mentions[i:i + bs]
        block = "\n".join(json.dumps({"id": m["id"], "source": m["source"], "text": m["text"][:1200]},
                                     ensure_ascii=False) for m in batch)
        prompt = (PROMPT.replace("{company}", profile.get("company", "")).replace("{category}", profile.get("category", ""))
                  .replace("{competitors}", ", ".join(competitors) or "none known").replace("{types}", ", ".join(TYPES))
                  .replace("{themes}", ", ".join(sorted(set(themes))[:40]) or "none yet").replace("{mentions}", block))
        try:
            out = complete_json(prompt, "tag", context={"batch": batch, "profile": profile})
        except RuntimeError:
            continue  # a failed batch is skipped, not guessed
        for item in out.get("items", []):
            m = by_id.get(item.get("id"))
            if not m or not item.get("relevant"):
                continue
            stats["relevant"] += 1
            for t in item.get("tags", [])[:3]:
                if t.get("type") not in TYPES:
                    stats["bad_type"] += 1
                    continue
                if not verify_quote(t.get("quote", ""), m["text"]):
                    stats["quotes_rejected"] += 1
                    continue
                theme = canon_theme(t.get("theme"))
                if not theme:
                    continue
                subj = t.get("subject") or m.get("subject_hint") or "category"
                if subj not in ("self", "category") and subj not in competitors:
                    subj = m.get("subject_hint") or "category"
                themes.append(theme)
                tags.append({"mention_id": m["id"], "type": t["type"], "theme": theme, "subject": subj,
                             "quote": t["quote"].strip(), "source": m["source"], "url": m["url"], "date": m.get("date", "")})
    stats["tags"] = len(tags)
    return {"tags": tags, "stats": stats}
