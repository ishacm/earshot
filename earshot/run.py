"""Run the whole pipeline: website -> profile -> mentions -> tags -> messaging -> report.

  python -m earshot.run --url https://example.com
  python -m earshot.run --url https://example.com --competitors "A,B" --csv reviews.csv
  EARSHOT_LLM=mock python -m earshot.run --demo          (fictional company, no network, no key)
"""
import argparse
import datetime as dt
import json
import re
from pathlib import Path

from earshot import ROOT, collect, llm, notify, profile, report, synthesize, tag

FIX = ROOT / "fixtures" / "demo"


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "run").lower()).strip("-")[:40] or "run"


def run(url: str, *, competitors: list[str] | None = None, terms: list[str] | None = None,
        csv_paths: list[str] | None = None, demo: bool = False, out_root: Path | None = None) -> dict:
    html = (FIX / "homepage.html").read_text() if demo else None
    fixtures = [json.loads(l) for l in (FIX / "mentions.jsonl").read_text().splitlines() if l.strip()] if demo else None
    prof = profile.build(url, html=html, overrides={"competitors": competitors, "search_terms": terms})
    col = collect.run(prof, csv_paths=csv_paths, fixtures=fixtures)
    tg = tag.run(prof, col["mentions"])
    sy = synthesize.run(prof, tg["tags"])
    result = {"created": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "mode": llm.mode(),
              "profile": prof, "collect": {"n": len(col["mentions"]), "sources": col["sources"], "capped": col["capped"]},
              "tag": {"stats": tg["stats"]}, "synth": sy, "llm_usage": dict(llm.USAGE)}
    out = (out_root or ROOT / "runs") / f"{dt.date.today()}-{slug(prof.get('company'))}"
    result["files"] = report.write(result, out)
    return result


def main():
    ap = argparse.ArgumentParser(description="Earshot: hear what customers actually say.")
    ap.add_argument("--url", default="https://ledgerly.example")
    ap.add_argument("--competitors", help="comma-separated, overrides the model's guess")
    ap.add_argument("--terms", help="comma-separated category search terms")
    ap.add_argument("--csv", action="append", help="your own export with a text column (repeatable)")
    ap.add_argument("--demo", action="store_true", help="fictional company + synthetic mentions, no network")
    ap.add_argument("--slack", action="store_true", help="post a summary to SLACK_WEBHOOK_URL")
    a = ap.parse_args()
    split = lambda s: [x.strip() for x in s.split(",") if x.strip()] if s else None
    r = run(a.url, competitors=split(a.competitors), terms=split(a.terms), csv_paths=a.csv, demo=a.demo)
    print(notify.summary_text(r))
    print(f"\nreport: {r['files']['markdown']}\n        {r['files']['html']}")
    if a.slack:
        print("slack:", "sent" if notify.slack(r) else "not sent (SLACK_WEBHOOK_URL missing or failed)")


if __name__ == "__main__":
    main()
