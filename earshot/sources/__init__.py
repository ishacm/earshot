"""Every source returns mentions: {id, source, url, date, text, query, rating?}.

Sources are public and free: Hacker News (Algolia API), Apple App Store reviews (iTunes RSS),
Reddit (official API, only if you add your own app credentials) and any CSV you export yourself
(for example reviews you are allowed to download from G2 or your own support tool).
We do not scrape sites whose terms forbid it.
"""
