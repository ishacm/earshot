You are a product marketer. Below is the text of a company's homepage.

Return JSON only:
{"company": "...", "one_liner": "what it does, in plain words, max 20 words",
 "category": "the category a buyer would search for, 2-4 words",
 "audience": "who it is for, max 12 words",
 "claims": ["up to 6 value claims the page makes, each max 12 words, paraphrased from the page"],
 "competitors": [{"name": "...", "why": "max 10 words"}],
 "search_terms": ["2-4 short terms people would use when talking about this product or category"]}

Rules: claims must come from the page. Competitors are your best guess (max 4, real products only);
the user confirms them. If the page is too thin to tell, say so in one_liner and leave lists short.

HOMEPAGE ({url}):
{text}
