from earshot.privacy import scrub
from earshot.tag import canon_theme, verify_quote

TEXT = "We moved to Ledgerly last year.  Receipt matching still breaks whenever a merchant name differs."


def test_exact_quote_passes_even_with_whitespace_and_case_differences():
    assert verify_quote("receipt matching still breaks whenever", TEXT)


def test_paraphrased_quote_is_rejected():
    assert not verify_quote("receipt matching is often broken", TEXT)


def test_too_short_quote_is_rejected():
    assert not verify_quote("Ledgerly", TEXT)


def test_curly_quotes_are_normalised():
    assert verify_quote("don’t trust the sync", "I don't trust the sync at all.")


def test_scrub_removes_people_but_keeps_meaning():
    out = scrub("Ask @jane_doe or mail jane@corp.com, call +49 170 1234567. See reddit.com/u/janedoe")
    assert "jane" not in out.lower() and "1234567" not in out
    assert "[email]" in out and "@[user]" in out and "[phone]" in out


def test_theme_labels_are_canonical():
    assert canon_theme("  Slow Month-End   Close!! ") == "slow month-end close"
