import json
from pathlib import Path

from fastapi.testclient import TestClient

from earshot.serve import app


def test_api_runs_demo():
    c = TestClient(app)
    assert c.get("/healthz").json() == {"ok": True}
    r = c.post("/run", json={"url": "https://ledgerly.example", "demo": True}).json()
    assert r["company"] == "Ledgerly" and r["top_pains"] and r["headlines"]


def test_n8n_workflow_is_valid_and_wired():
    wf = json.loads(Path("n8n/earshot.workflow.json").read_text())
    names = {n["name"] for n in wf["nodes"]}
    for src, conns in wf["connections"].items():
        assert src in names
        for branch in conns["main"]:
            for c in branch:
                assert c["node"] in names
    assert not any("hooks.slack.com/services/" in json.dumps(n) for n in wf["nodes"]), "no real webhook URLs in the repo"


def test_api_token_is_enforced_when_set(monkeypatch):
    c = TestClient(app)
    monkeypatch.setenv("EARSHOT_API_TOKEN", "s3cret-for-tests")
    assert c.get("/healthz").status_code == 401
    assert c.get("/healthz", headers={"X-Api-Token": "s3cret-for-tests"}).status_code == 200
