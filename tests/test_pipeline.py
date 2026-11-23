import json

import pytest

from earshot import collect, llm, synthesize
from earshot.run import run


def test_demo_run_end_to_end(tmp_path):
    r = run("https://ledgerly.example", demo=True, out_root=tmp_path)
    assert r["mode"] == "mock"
    assert r["collect"]["n"] == 32
    assert r["tag"]["stats"]["quotes_rejected"] == 0
    m = r["synth"]["messaging"]
    assert len(m["headlines"]) == 3 and m["battlecards"]
    md = open(r["files"]["markdown"]).read()
    assert "Demo data." in md and "model guess, please confirm" in md
    assert "<html" in open(r["files"]["html"]).read()


def test_every_quote_in_the_report_exists_in_a_source(tmp_path):
    r = run("https://ledgerly.example", demo=True, out_root=tmp_path)
    texts = [json.loads(l)["text"].lower() for l in open("fixtures/demo/mentions.jsonl")]
    for e in r["synth"]["evidence"]:
        assert any(" ".join(e["quote"].lower().split()) in " ".join(t.split()) for t in texts), e["quote"]


def test_counts_are_mentions_not_quotes():
    tags = [{"mention_id": "m1", "type": "pain", "theme": "x", "subject": "self", "quote": "a b c", "source": "hn", "url": "", "date": ""},
            {"mention_id": "m1", "type": "pain", "theme": "x", "subject": "self", "quote": "a b c d", "source": "hn", "url": "", "date": ""},
            {"mention_id": "m2", "type": "pain", "theme": "x", "subject": "self", "quote": "e f g", "source": "hn", "url": "", "date": ""}]
    th = synthesize.themes(tags)
    assert th[0]["mentions"] == 2 and th[0]["weak"] is True


def test_uncited_messaging_is_dropped(monkeypatch):
    tags = [{"mention_id": f"m{i}", "type": "pain", "theme": "slow close", "subject": "self", "quote": f"close takes days {i}",
             "source": "hn", "url": "", "date": ""} for i in range(4)]
    fake = {"positioning": {"for": "x", "evidence": ["E99"]},
            "headlines": [{"text": "cited", "evidence": ["E1"]}, {"text": "made up", "evidence": []}],
            "pillars": [], "objections": [{"objection": "o", "evidence": ["E404"]}], "battlecards": []}
    monkeypatch.setattr(synthesize, "complete_json", lambda *a, **k: json.loads(json.dumps(fake)))
    out = synthesize.run({"company": "X"}, tags)
    assert [h["text"] for h in out["messaging"]["headlines"]] == ["cited"]
    assert out["messaging"]["positioning"] is None and out["messaging"]["objections"] == []
    assert out["dropped_uncited"] == 3


def test_no_evidence_means_no_messaging():
    out = synthesize.run({"company": "X"}, [])
    assert out["messaging"] is None and "Not enough" in out["note"]


def test_collect_dedupes_scrubs_and_caps():
    fx = [{"id": "a", "source": "hn", "url": "", "text": "Mail me at bob@x.com because the export is broken again today."},
          {"id": "b", "source": "hn", "url": "", "text": "Mail me at bob@x.com because the export is broken again today."},
          {"id": "c", "source": "hn", "url": "", "text": "too short"}]
    out = collect.run({"company": "X"}, fixtures=fx)
    assert len(out["mentions"]) == 1 and "bob@" not in out["mentions"][0]["text"]


def test_queries_cover_product_competitors_and_category():
    q = collect.queries({"company": "Ledgerly", "competitors": [{"name": "Northbook"}], "search_terms": ["expense tool", "ledgerly"]})
    assert q == [("Ledgerly", "self"), ("Northbook", "Northbook"), ("expense tool", "category")]


def test_paid_provider_is_refused_without_opt_in(monkeypatch):
    monkeypatch.delenv("EARSHOT_ALLOW_PAID", raising=False)
    with pytest.raises(llm.PaidProviderError):
        llm.check_cost({"id": "anthropic", "paid": True})
    llm.check_cost({"id": "groq"})  # free provider is fine


def test_live_mode_without_key_fails_clearly(monkeypatch):
    monkeypatch.setenv("EARSHOT_LLM", "live")
    monkeypatch.setenv("EARSHOT_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY is not set"):
        llm._call(llm.provider(), "m", "hi", 10)
