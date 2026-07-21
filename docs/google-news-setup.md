# Google News setup — consulting24.co

Built 2026-07-22. Covers what is now live in the repo, the owner-only steps that remain,
and an honest read on what to expect.

## What Google actually requires in 2026

There is no application form any more. Google removed manual submission in 2019: sites are
considered for Top stories and the News tab automatically, through normal crawling, provided
they produce genuine news and meet the Google News content policies. Publisher Center is not
an approval gate; it controls how the publication is presented and lets you define sections.

So the lever is not "apply". The lever is: publish real, dated, sourced news, mark it up as
`NewsArticle`, expose it in a news sitemap, and be transparent about who is publishing it.

Policy points that bind this site specifically:

- **Transparency** — clear dates and bylines, information about the author, publication and
  publisher, and contact information. Covered by `/editorial-policy/`, `/about/`, `/contact/`
  and the per-item byline.
- **Ads and sponsored content** — paid promotional material must not exceed the content.
  Each news item carries exactly one CTA card. Do not add more.
- **Misleading content** — the headline and standfirst must reflect the body.

## What is live in the repo

| Piece | Path | Notes |
|---|---|---|
| News desk CLI | `scripts/news.py` | new / publish / build / list / correct / wire |
| Item store | `config/news_items.json` | single source of truth, rebuild is idempotent |
| Drafts | `news/_drafts/*.md` | not published, not crawled |
| News hub | `/news/` | reverse-chronological, dated, bylined |
| News items | `/news/<slug>/` | `NewsArticle` schema, visible primary-source box |
| News sitemap | `/news-sitemap.xml` | last 48h only, auto-ages, in `robots.txt` |
| RSS feed | `/news/feed.xml` | last 20 items, for the Publisher Center section |
| Editorial policy | `/editorial-policy/` | sourcing, corrections, funding, AI disclosure |
| Footer links | all 950 pages | `news.py wire`, idempotent |

`scripts/publish.py` calls `news.py build` before it writes `sitemap.xml`, so the daily
pipeline keeps the 48-hour window correct on its own. Nobody has to remember to remove
stale items.

## Publishing an item

```bash
python3 scripts/news.py new "Headline as it should read"
# fill in news/_drafts/<slug>.md, then
python3 scripts/news.py publish <slug>
git add -A && git commit -m "News: <headline>" && git push origin main
```

`publish` refuses the item unless it has a named primary source and a `source_url` that
actually resolves, a 60-300 char standfirst, a headline under 110 chars, and at least 120
words. It also refuses any item containing the fabrication markers from the July 2026
incident (AFIP, Law 697, Law 61 of 2023, Law 164 of 2020, "Panama Financial Innovation Law",
SSNF-as-licensor). That gate exists because this site has already published invented laws
and invented regulators once. Do not weaken it.

To correct something after the fact:

```bash
python3 scripts/news.py correct <slug> "What was wrong and what it now says"
```

That appends a dated, visible correction and bumps `dateModified`. Never silently edit a
published item, and never delete one to hide an error.

## Owner steps that remain

1. **Submit the news sitemap in Search Console.** Property `www.consulting24.co` is already
   verified via the `google-site-verification` meta tag on the homepage. Add
   `news-sitemap.xml` under Sitemaps. It will show few or zero URLs whenever nothing was
   published in the last two days; that is correct behaviour, not an error.

2. **Create the publication in Publisher Center** (<https://publishercenter.google.com>).
   - Publication name: **Consulting24** — this must match `<news:name>` in the news sitemap
     exactly. It is set by `PUB_NAME` in `scripts/news.py`. If you rename the publication,
     change it in both places or the sitemap becomes invalid.
   - Website URL: `https://www.consulting24.co`
   - Verify ownership: Publisher Center reads the Search Console verification, so sign in
     with the Google account that owns the Search Console property.
   - Add a section pointing at `https://www.consulting24.co/news/feed.xml`.
   - Fill in the contact and about details; they should agree with `/editorial-policy/`.

3. **Keep a cadence.** A news section with three items from 2026 will not be treated as a
   news source. Realistically this needs something in the region of one to three sourced
   items a week, every week, before Google has any reason to treat the site as a publisher.

## What to expect, honestly

consulting24.co is a commercial licensing site, not a newsroom, and Google knows the
difference. Two realistic outcomes:

- **Likely:** the `/news/` section earns fresh-crawl behaviour, ranks for "MiCA deadline",
  "CASP authorisation" style queries where the site is currently invisible, and gets cited by
  AI answer engines because each item links a primary regulator source. That is worth having
  on its own, and it directly attacks the audit's finding #1 (zero visibility for the EU/MiCA
  cluster).
- **Less likely:** actual Top stories placement. That competes with Reuters, CoinDesk and law
  firms with far more authority, and it needs sustained original reporting rather than
  summaries of published statements.

Treat Google News as a by-product of publishing genuinely useful sourced regulatory news, not
as the goal. The sourcing discipline is what makes the section worth reading either way.

## Do not

- Do not point the DeepSeek generator at `/news/`. Regulatory news is the highest-risk
  content type on this site, and the generator has already invented four laws and two
  regulators. News items are written by a person against a source that has been read.
- Do not add more than one CTA per item (Google News: ads must not exceed content).
- Do not backdate `published`. It is set once, on first publish, and never rewritten.
