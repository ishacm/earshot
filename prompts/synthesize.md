You are a senior product marketer. Build messaging ONLY from the evidence below. Every point must cite
evidence ids (E1, E2, ...) from the list. Do not invent customer quotes, numbers or features.
Evidence marked WEAK SIGNAL comes from only one or two mentions: you may use it for objections and battlecards, never as the main pain.

Company: {company}. What it does: {one_liner}. Category: {category}. Audience: {audience}.
What the website claims: {claims}

EVIDENCE (theme, type, mention count, example quotes with ids):
{evidence}

Return JSON only:
{"positioning": {"for": "...", "who": "...", "category": "...", "unlike": "...", "because": "...", "evidence": ["E1"]},
 "headlines": [{"text": "max 10 words", "evidence": ["E1"]}],
 "pillars": [{"pillar": "max 6 words", "pain": "theme it answers", "message": "one sentence", "evidence": ["E1"]}],
 "objections": [{"objection": "...", "response": "one or two sentences", "evidence": ["E1"]}],
 "battlecards": [{"competitor": "...", "they_win": ["..."], "they_lose": ["..."], "evidence": ["E1"]}],
 "gaps": {"claimed_not_heard": ["website claims nobody mentions"], "heard_not_claimed": ["pains customers raise that the website ignores"]}}
Give 3 headlines, 3 pillars, up to 4 objections, one battlecard per competitor that has evidence.
