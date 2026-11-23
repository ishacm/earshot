"""Optional: post a short summary to Slack via an incoming webhook (SLACK_WEBHOOK_URL)."""
import os


def summary_text(run: dict) -> str:
    p, sy = run["profile"], run["synth"]
    top = [t for t in sy["themes"] if t["type"] == "pain" and not t["weak"]][:3]
    lines = [f"*Earshot: {p.get('company')}* ({run['collect']['n']} mentions, {run['tag']['stats']['tags']} verified quotes)"]
    lines += [f"• top pain: {t['theme']} ({t['mentions']} mentions)" for t in top]
    m = sy.get("messaging") or {}
    if m.get("headlines"):
        lines.append(f"• headline to test: “{m['headlines'][0]['text']}”")
    gaps = (m.get("gaps") or {}).get("heard_not_claimed") or []
    if gaps:
        lines.append(f"• missing from the website: {gaps[0]}")
    return "\n".join(lines)


def slack(run: dict) -> bool:
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        return False
    import httpx
    try:
        return httpx.post(url, json={"text": summary_text(run)}, timeout=15).status_code == 200
    except Exception:
        return False
