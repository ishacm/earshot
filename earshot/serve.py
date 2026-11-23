"""A tiny local API so n8n (or anything else) can trigger runs.

  uvicorn earshot.serve:app --port 8090
  POST /run  {"url": "...", "competitors": ["A", "B"], "demo": false}   -> summary + report paths
Localhost only by default. If n8n runs in Docker, start it with --host 0.0.0.0 AND set EARSHOT_API_TOKEN.
"""
import hmac
import os

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from earshot import notify
from earshot.run import run

def require_token(x_api_token: str | None = Header(default=None)):
    """If EARSHOT_API_TOKEN is set, every call must send it as the X-Api-Token header. Set it whenever the API listens
    beyond localhost (for example --host 0.0.0.0 so n8n in Docker can reach it)."""
    want = os.environ.get("EARSHOT_API_TOKEN")
    if want and not hmac.compare_digest(x_api_token or "", want):
        raise HTTPException(status_code=401, detail="missing or wrong X-Api-Token")


app = FastAPI(title="Earshot", dependencies=[Depends(require_token)])


class RunIn(BaseModel):
    url: str
    competitors: list[str] | None = None
    terms: list[str] | None = None
    demo: bool = False


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/run")
def run_endpoint(body: RunIn):
    r = run(body.url, competitors=body.competitors, terms=body.terms, demo=body.demo)
    m = r["synth"].get("messaging") or {}
    return {"company": r["profile"].get("company"), "summary": notify.summary_text(r),
            "mentions": r["collect"]["n"], "verified_quotes": r["tag"]["stats"]["tags"],
            "top_pains": [t["theme"] for t in r["synth"]["themes"] if t["type"] == "pain" and not t["weak"]][:5],
            "headlines": [h["text"] for h in m.get("headlines", [])], "files": r["files"]}
