"""Step 5: write the findings as Markdown (for GitHub) and a self-contained HTML page (to share)."""
import html
import json
from pathlib import Path

LABEL = {"pain": "Pains", "job": "Jobs to be done", "objection": "Objections", "praise": "What people like",
         "switch_trigger": "Why people switch", "feature_request": "What people ask for"}


def _q(q: dict) -> str:
    src = f"{q['source']}{', ' + q['date'] if q.get('date') else ''}"
    return f'> "{q["quote"]}"  \n> [{src}]({q["url"]})' if q.get("url") else f'> "{q["quote"]}" ({src})'


def markdown(run: dict) -> str:
    p, col, tg, sy = run["profile"], run["collect"], run["tag"], run["synth"]
    L = [f"# What people say about {p.get('company')} and its category",
         f"*{p.get('one_liner', '')}*  ", f"Category: **{p.get('category', '')}** · audience: {p.get('audience', '')}",
         "", f"**Run:** {run['created']} · mode: `{run['mode']}` · {col['n']} mentions collected, "
         f"{tg['stats']['relevant']} relevant, {tg['stats']['tags']} tagged quotes, "
         f"{tg['stats']['quotes_rejected']} quotes rejected as not verbatim, {sy['dropped_uncited']} uncited claim(s) dropped.", ""]
    if run["mode"] == "mock":
        L += ["> **Demo data.** This run used the fictional fixture company and synthetic mentions. "
              "It shows the format, not findings.", ""]
    comp = ", ".join(c["name"] for c in p.get("competitors", [])) or "none"
    L += [f"Competitors: {comp} ({'confirmed by user' if p.get('competitors_confirmed') else 'model guess, please confirm'})", ""]
    m = sy.get("messaging")
    if m:
        ev = {e["id"]: e for e in sy["evidence"]}
        cite = lambda ids: " ".join(f"[{i}]" for i in ids)
        L += ["## Messaging, built from the evidence", ""]
        pos = m.get("positioning")
        if pos:
            L += [f"**Positioning.** For {pos.get('for')} who {pos.get('who')}, {p.get('company')} is the {pos.get('category')} "
                  f"that {pos.get('because')}. Unlike {pos.get('unlike')}. {cite(pos['evidence'])}", ""]
        L += ["**Headline options**", ""] + [f"- {h['text']} {cite(h['evidence'])}" for h in m["headlines"]] + [""]
        L += ["| Pillar | Answers this pain | Message | Evidence |", "|---|---|---|---|"]
        L += [f"| {x['pillar']} | {x.get('pain', '')} | {x.get('message', '')} | {cite(x['evidence'])} |" for x in m["pillars"]]
        L += ["", "**Objections and answers**", ""]
        L += [f"- **{o['objection']}** {o.get('response', '')} {cite(o['evidence'])}" for o in m["objections"]]
        if m.get("battlecards"):
            L += ["", "## Battlecards", ""]
            for b in m["battlecards"]:
                L += [f"### vs {b['competitor']} {cite(b['evidence'])}", "",
                      "| Where they win | Where they lose |", "|---|---|"]
                w, l = b.get("they_win", []), b.get("they_lose", [])
                L += [f"| {w[i] if i < len(w) else ''} | {l[i] if i < len(l) else ''} |" for i in range(max(len(w), len(l)))]
                L += [""]
        g = m.get("gaps") or {}
        L += ["## Message-market gap", "", "**Claimed on the website, rarely heard from customers**", ""]
        L += [f"- {x}" for x in g.get("claimed_not_heard", [])] or ["- none found"]
        L += ["", "**Raised by customers, missing from the website**", ""]
        L += [f"- {x}" for x in g.get("heard_not_claimed", [])] or ["- none found"]
        L += ["", "## Evidence", ""] + [f"**[{i}]** {e['type']} · {e['theme']}{' · weak signal' if e.get('weak') else ''}\n{_q(e)}\n" for i, e in ev.items()]
    else:
        L += [f"> {sy.get('note', 'No messaging produced.')}", ""]
    L += ["## All themes", "", "| Type | Theme | Mentions | About | Signal |", "|---|---|---|---|---|"]
    for t in sy["themes"][:40]:
        about = ", ".join(f"{k} ({v})" for k, v in t["subjects"].items())
        L += [f"| {LABEL.get(t['type'], t['type'])} | {t['theme']} | {t['mentions']} | {about} | {'weak' if t['weak'] else 'ok'} |"]
    L += ["", "## Sources", ""] + [f"- {k}: {v}" for k, v in col["sources"].items()]
    L += ["", "*Counts are mentions in this sample, not market share. Small samples are marked weak. "
          "Usernames, emails and phone numbers were removed before analysis.*"]
    return "\n".join(L)


def html_page(md: str, title: str) -> str:
    """Tiny Markdown subset -> HTML, so the report has zero dependencies and opens anywhere."""
    import re
    out, in_table, in_list = [], False, False
    def inline(s):
        s = html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
        s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
        return re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', s)
    for line in md.splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            if not in_table:
                out.append("<table>"); in_table = True
                out.append("<tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr>"); continue
            out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>"); continue
        if in_table:
            out.append("</table>"); in_table = False
        if line.startswith("- "):
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{inline(line[2:])}</li>"); continue
        if in_list:
            out.append("</ul>"); in_list = False
        if line.startswith("#"):
            n = len(line) - len(line.lstrip("#"))
            out.append(f"<h{n}>{inline(line[n:].strip())}</h{n}>")
        elif line.startswith(">"):
            out.append(f"<blockquote>{inline(line.lstrip('> ').rstrip())}</blockquote>")
        elif line.strip():
            out.append(f"<p>{inline(line.rstrip())}</p>")
    if in_table: out.append("</table>")
    if in_list: out.append("</ul>")
    css = ("body{font:16px/1.6 system-ui,sans-serif;max-width:860px;margin:40px auto;padding:0 20px;color:#1b1a18;background:#f5f1e8}"
           "h1{font-weight:600;letter-spacing:-.02em}h2{margin-top:40px;border-top:1px solid #dad3c5;padding-top:20px}"
           "table{border-collapse:collapse;width:100%;font-size:14px}td,th{border-bottom:1px solid #dad3c5;padding:8px;text-align:left;vertical-align:top}"
           "blockquote{margin:6px 0 14px;padding-left:14px;border-left:3px solid #b04e1a;color:#3b3934}a{color:#b04e1a}"
           "code{background:#ebe5d8;padding:1px 4px;border-radius:3px}")
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>{css}</style></head><body>{"".join(out)}</body></html>'


def write(run: dict, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    md = markdown(run)
    (out_dir / "report.md").write_text(md)
    (out_dir / "report.html").write_text(html_page(md, f"Earshot: {run['profile'].get('company')}"))
    (out_dir / "run.json").write_text(json.dumps(run, indent=2, ensure_ascii=False))
    return {"markdown": str(out_dir / "report.md"), "html": str(out_dir / "report.html"), "json": str(out_dir / "run.json")}
