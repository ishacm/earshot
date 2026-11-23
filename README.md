# Earshot 👂

[![tests](https://github.com/ishacm/earshot/actions/workflows/ci.yml/badge.svg)](https://github.com/ishacm/earshot/actions/workflows/ci.yml)
![cost](https://img.shields.io/badge/runs%20at-%E2%82%AC0-22c55e)
![license](https://img.shields.io/badge/license-MIT-blue)

**Paste a company's website. Get back what its customers (and its competitors' customers) actually say: the top pains, jobs to be done, objections and reasons people switch, plus messaging and battlecards built only from real quotes.**

*Every quote is checked word for word against its source. Anything the model can't back up gets dropped.*

---

## Why this exists

Most messaging is written from the inside out: what the team thinks is special. Customers talk about something else, in different words, in public, every day. Earshot listens there first, then writes the messaging.

It's built for product marketers, founders and GTM teams at any startup. Works for B2B SaaS, dev tools, consumer apps, anything people talk about online.

## What you get

One report (Markdown + a shareable HTML page) with:

| Section | What's in it |
|---|---|
| **Messaging** | Positioning statement, 3 headline options, 3 pillars, each tied to a pain and to the quotes that prove it |
| **Objections** | What makes people hesitate, and an answer grounded in what customers said |
| **Battlecards** | Per competitor: where they win, where they lose, with evidence |
| **Message-market gap** | What your website claims that nobody mentions, and what customers raise that your website ignores |
| **Themes** | Every pain, job, objection, praise, switching trigger and feature request, counted by mentions, with weak signals marked |
| **Evidence** | Every quote, linked to its source and date |

## How it works

```
website ──► profile ──► collect ──► tag ──► synthesize ──► report
            category,    HN, App     pains,   counts in code,   Markdown,
            claims,      Store,      jobs,    messaging by      HTML,
            competitors  Reddit,     quotes   the model, only   Slack
            (you confirm) your CSV   (verified) from evidence
```

1. **Profile** reads the homepage: what it does, the category, the claims it makes, and a first guess at competitors. You can confirm or override the competitors.
2. **Collect** pulls public mentions of the product, each competitor and the category from free, official sources, then removes usernames, emails and phone numbers.
3. **Tag** labels each mention with pains, jobs, objections, praise, switching triggers and feature requests. Every quote must be an exact substring of the original text, or it's rejected and counted.
4. **Synthesize** counts themes in code (so numbers are reproducible), then asks the model to write messaging using numbered evidence only. Anything that cites no valid evidence is dropped.
5. **Report** writes Markdown and HTML, and can post a summary to Slack.

## Try it in 60 seconds

No API key, no account, no network:

```bash
git clone https://github.com/ishacm/earshot && cd earshot
pip install -r requirements.txt pytest
EARSHOT_LLM=mock python -m earshot.run --demo    # a fictional company, "Ledgerly"
EARSHOT_LLM=mock pytest -q                       # 21 tests
```

Then open `runs/<date>-ledgerly/report.html`.

> The demo uses a fictional company and synthetic mentions, and mock mode swaps the AI for simple rules. It shows the format and proves the plumbing. It is not a finding about any real product.

## Run it for real (still €0)

```bash
cp .env.example .env          # add a free Groq key from console.groq.com (never committed)
python -m earshot.run --url https://your-company.com --competitors "Rival A, Rival B"
python -m earshot.run --url https://your-company.com --csv my_g2_export.csv   # add your own reviews
```

| Source | Cost | Notes |
|---|---|---|
| Hacker News | free | Public Algolia API, no key |
| Apple App Store reviews | free | Public iTunes feed, only for products with an iOS app |
| Reddit | free | Official API, only if you add your own `REDDIT_CLIENT_ID/SECRET` |
| Your CSV | free | Any export with a text column: G2, support tickets, NPS comments, sales call notes |
| AI | free | Groq free tier by default. Paid providers are refused unless `EARSHOT_ALLOW_PAID=true` |

Earshot only uses official APIs and files you provide. It does not scrape sites whose terms forbid it.

## Automate it with n8n

Self-hosted n8n (the free Community Edition) can run Earshot on demand or every Monday and post the summary to Slack:

```bash
uvicorn earshot.serve:app --port 8090                                   # n8n on the same machine
EARSHOT_API_TOKEN=pick-a-long-random-string \
  uvicorn earshot.serve:app --host 0.0.0.0 --port 8090                  # n8n in Docker: always set a token
```

Import [`n8n/earshot.workflow.json`](n8n/earshot.workflow.json) into n8n. It has two triggers:

- **Webhook:** `POST /webhook/earshot {"url": "https://...", "competitors": "A, B"}` runs it for any company, for example from a form or a Slack command.
- **Every Monday 07:00:** re-runs for the company you set, so you can watch themes change over time.

Paste your token into the `X-Api-Token` header of the *Run Earshot* node, and your Slack incoming-webhook URL into the last node (or delete it).

## Safety rails 🛡️

- **Quotes are verbatim or gone.** The report shows how many quotes were rejected and how many uncited claims were dropped.
- **Counts are honest.** They are mentions in this sample, not market share, and themes with fewer than 3 mentions are marked weak.
- **People are not the point.** Usernames, emails and phone numbers are stripped before anything is stored.
- **No secrets in code.** Keys live in `.env` (git-ignored), and CI fails if anything key-shaped is committed.
- **No surprise bills.** Paid AI providers are blocked unless explicitly allowed.

## Before quoting any number

Everything in this repo runs on a fictional demo company, so nothing here is a finding yet. On real data, check the tagging by hand on a sample of 30 mentions before you trust the themes, and always quote counts as "mentions in this sample", with the date and sources. The report prints both for you.

## Repo map

```
earshot/     pipeline: profile, collect, tag, synthesize, report, serve (API for n8n)
  sources/   hackernews, appstore, reddit, csv
prompts/     the three prompts, versioned in git
fixtures/    the fictional demo company and its synthetic mentions
n8n/         importable workflow
tests/       21 tests, run in mock mode on every push
```

---

<sub>MIT licensed · built by [Isha Chaudhari](https://github.com/ishacm) · part of a small set of open GTM tools, alongside [Kompass](https://github.com/ishacm/kompass) and [crm-tidy](https://github.com/ishacm/crm-tidy)</sub>
