"""Your own export: any CSV with a text column (text/review/body/comment). Optional: source, url, date, rating."""
import csv
import hashlib
from pathlib import Path

TEXT_COLS = ("text", "review", "body", "comment", "content", "feedback")


def load(path: str | Path, query: str = "") -> list[dict]:
    out = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = {c.lower().strip(): c for c in (reader.fieldnames or [])}
        tcol = next((cols[c] for c in TEXT_COLS if c in cols), None)
        if not tcol:
            raise ValueError(f"{path}: no text column found (expected one of {', '.join(TEXT_COLS)})")
        for i, row in enumerate(reader):
            text = (row.get(tcol) or "").strip()
            if not text:
                continue
            rid = hashlib.sha1(f"{path}:{i}:{text[:50]}".encode()).hexdigest()[:10]
            rating = row.get(cols.get("rating", ""), "") if "rating" in cols else ""
            out.append({"id": f"csv-{rid}", "source": row.get(cols.get("source", ""), "") or "csv",
                        "url": row.get(cols.get("url", ""), "") or "", "date": row.get(cols.get("date", ""), "") or "",
                        "text": text, "query": query, "rating": int(rating) if str(rating).isdigit() else None})
    return out
