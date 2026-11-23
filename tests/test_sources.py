import json

from earshot.sources import appstore, csvfile, hn


def test_hn_parse_strips_html_and_builds_links():
    data = {"hits": [{"objectID": "123", "created_at": "2026-10-01T10:00:00Z",
                      "comment_text": "<p>Setup took &quot;six weeks&quot;</p>"}, {"objectID": "9", "comment_text": ""}]}
    out = hn.parse(data, "Quillsum")
    assert len(out) == 1
    assert out[0]["text"] == 'Setup took "six weeks"'
    assert out[0]["url"].endswith("id=123") and out[0]["date"] == "2026-10-01"


def test_appstore_parse_skips_app_entry_and_reads_rating():
    data = {"feed": {"entry": [{"im:name": {"label": "App"}},
                               {"id": {"label": "77"}, "title": {"label": "Crashes"}, "content": {"label": "Every upload."},
                                "im:rating": {"label": "2"}, "updated": {"label": "2026-10-02T00:00:00-07:00"}}]}}
    out = appstore.parse(data, 555, "Ledgerly")
    assert len(out) == 1 and out[0]["rating"] == 2 and out[0]["text"] == "Crashes. Every upload"


def test_csv_needs_a_text_column(tmp_path):
    good = tmp_path / "r.csv"
    good.write_text("Review,Rating,URL\nGreat tool but pricey,4,https://x\n,5,\n")
    out = csvfile.load(good)
    assert len(out) == 1 and out[0]["rating"] == 4 and out[0]["url"] == "https://x"
    bad = tmp_path / "b.csv"
    bad.write_text("name,score\na,1\n")
    try:
        csvfile.load(bad)
        assert False, "should have raised"
    except ValueError as e:
        assert "no text column" in str(e)
