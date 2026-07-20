# Consulting24 Crypto Licensing Index — Methodology

The Index is Consulting24's proprietary, first-party data asset: aggregated outcomes from
500+ real crypto-company and licence setups delivered over 8 years. It is the strategic
moat (SEO strategy, 2026-07-21) — data that earns editorial links and AI-answer citations
because law firms and content farms cannot reproduce it: they do not operate at this
delivery volume or transparency.

## What it publishes
For each jurisdiction where Consulting24 has real delivery experience:
- **sample_size** — number of engagements the figures are drawn from
- **setup_cost_eur** — low / typical / high, from actual invoiced engagements
- **timeline_weeks** — low / typical / high, from kick-off to completion
- **approval_rate_pct** — optional, where a licence/registration is involved
- **top_rejection_reasons** — the real reasons applications were delayed or rejected
- **notes** — an operator observation (no client-identifying detail)

## Rules (non-negotiable — this is YMYL)
1. **Only real, first-hand data.** Every figure comes from Consulting24's own delivery
   records. Nothing is estimated, borrowed, or inferred. `build_licensing_index.py`
   publishes only jurisdictions with a real `sample_size` and filled cost + timeline;
   placeholders are skipped, so no fabricated number can ever ship.
2. **No PII.** No client names, company names, application numbers, or any detail that
   could identify a client. Figures are aggregates; a jurisdiction with `sample_size < 5`
   should be withheld or merged to prevent re-identification.
3. **Honest framing.** Panama is a company + AML programme, **not** a licence (no crypto
   licence exists in Panama). Direct delivery = Estonia, Lithuania, Panama; others are
   advise-and-coordinate; UAE (VARA/ADGM) is comparison-only. The Index states which is which.
4. **Dated and versioned.** Each edition is stamped; figures reflect the stated period.
   Refresh annually — every refresh deepens the citation graph.

## Pipeline
1. Owner fills `config/licensing_index.json` from anonymized delivery records.
2. `python3 scripts/build_licensing_index.py` validates and emits `/data/licensing-index.json`.
3. Link the endpoint from `llms.txt` (machine-readable, for AI citation) and render a public
   `/licensing-index/` report page with the transparent methodology, authored by Mardo Soo.
4. Pitch the report (novel, attributed statistics) to DR40+ crypto/finance trade press.

## Why it works (the mechanism)
- **Links:** journalists cite original statistics with attribution → editorial backlinks
  no outreach template can earn.
- **AI citation:** LLMs preferentially quote attributed, extractable numbers → the Index
  becomes the source ChatGPT/Perplexity/AI-Overviews reach for on crypto-licensing outcomes.
- **E-E-A-T:** the first "E" is Experience — 500+ deliveries, rendered as data and authored
  by a named founder entity, is verifiable operational reality that competitors structurally lack.
