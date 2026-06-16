# Google Search Console — diagnosis & fix plan (2026-06-14)

Snapshot from GSC **Page indexing** for `https://www.consulting24.co/`:

- **Indexed: 250**  ·  **Not indexed: 787**  (~24% of known URLs indexed by Google)
- Note: the in-repo `index_monitor.py` "94% indexed" figure is **Bing-only** (checks Bing's `url:` operator). Google is the gap.

## Not-indexed breakdown & root cause

| Reason | Count | Source | Root cause | Status |
|---|---:|---|---|---|
| Discovered – currently not indexed | 514 | Google | **Current programmatic pages**, never crawled (all "Last crawled: N/A"). Crawl-budget starvation: ~1,000 URLs added fast + low domain authority + budget wasted on dead Wix URLs. | Addressed indirectly (below) |
| Crawled – currently not indexed | 187 | Google | Mostly **legacy Wix URLs** (`/post/*`, `/blog/tags/*`, `?lang=no`) crawled Apr–May before migration; thin/stale. Some quality-borderline. | Redirects + quality fixes |
| Not found (404) | 55 | Website | **Legacy Wix URLs** still in Google's index: `/post/*`, `/blog/tags/*`, `/profile/*` forum spam, old slugs (`/crypto-license-dubai`), `?lang=no` variants. | ✅ Redirects added |
| Duplicate, Google chose different canonical | 11 | Google | Trailing-slash / lang / old-vs-new variants. | Canonical already self-referential; monitor |
| Page with redirect | 8 | Website | Sitemap/links pointing at redirecting URLs. | ✅ sitemap excludes stubs |
| Blocked due to other 4xx | 8 | Website | Old URLs returning 4xx. | Drop naturally |
| Excluded by 'noindex' | 3 | Website | Intended (404 page, redirect stubs). | ✅ correct |
| Alternate page w/ proper canonical | 1 | Website | Canonical working. | ✅ correct |

**One-line story:** the site is carrying ~250+ dead URLs from the **old Wix site**, which (a) sit as 404/crawled-not-indexed and (b) burn the crawl budget that should be spent on the **514 real pages Google hasn't crawled yet**.

## What was fixed in this change

1. **Legacy-Wix 404 cleanup → 46 301-equivalent redirect stubs** (`config/redirects.json` + `scripts/redirects.py`).
   - Old slugs/posts/tags with a modern equivalent now redirect (consolidates their signals; stops 404 crawl waste).
   - `?lang=no` variants are caught by the same path stub.
   - Junk left to 404 on purpose so Google drops it: `/profile/*` forum spam, off-topic crypto-news posts.
2. **Title de-duplication on 326 live pages** — killed `... Crypto License: Crypto X` junk titles (CTR + scaled-content signal). Root cause also fixed in `scripts/generate.py` (token-coverage keyword check) so future pages are clean.
3. **E-E-A-T retrofit** — injected "Official/Primary sources" (regulator citations) where missing; Article author/date schema universal; `href="//"` homepage-link bug fixed.
4. **Fresh sitemap** (`scripts/publish.py`) — 848 URLs, redirect stubs + noindex excluded, lastmod refreshed → recrawl signal. IndexNow pinged (Bing/Yandex).

## Remaining plan (owner actions)

### P0 — concentrate Google's crawl budget on the 514
- In GSC **URL Inspection → Request indexing** for the top ~20 money pages (jurisdiction + activity hubs). Manual, ~10/day cap.
- Keep the daily pipeline pushing fresh `lastmod`; don't add new bulk pages until the 514 backlog clears.
- (Optional) Google **Indexing API** works in practice for many URL types — wire a submitter reusing the IndexNow loop pattern if you want to accelerate.

### P1 — raise average page quality (why "discovered/crawled" pages stay unindexed)
- The 600 activity×country pages share heavy boilerplate. Two levers:
  - **Differentiate**: per-jurisdiction regulator detail, real timelines, a unique paragraph; remove the "we deliver directly" claim on advisory-only jurisdictions.
  - **Consolidate the thinnest**: Google indexing 250 and ignoring 514 is a "too many thin pages for this authority" signal. Pruning/merging the weakest long-tail combos into stronger hubs can lift the rest.

### P2 — monitoring & hygiene
- Validate the redirect fixes in GSC (each reason → **Validate Fix**) once deployed.
- Watch the **Duplicate canonical (11)** bucket; if it's trailing-slash, enforce one form in internal links.
- Re-pull GSC in ~2–4 weeks; expect 404/crawled-not-indexed to fall and indexed count to climb as budget frees up.

---

# Performance analysis (2026-06-15) — the click problem

Full GSC Performance pull (3 months, Web):

- **361K impressions · 100 clicks · CTR ~0.03% · avg position 38.9.** No manual action (clean). Huge impression base, page-4 average rank, almost zero clicks.
- **Core Web Vitals:** "not enough field data" (low traffic) — site is static/fast, no CWV work needed.
- **Links:** only **369 external backlinks** (mostly to `/`; top referrers islington.gov.uk, medium.com). Low domain authority is the root cause of the ~39 average position.

### The legacy-URL authority transfer (highest ROI on-site lever)
The top pages by impressions are **old Wix URLs**, not the new pages — Google still holds their authority:

| Legacy URL | Impressions | Pos | Redirect |
|---|---:|---:|---|
| /dubai-crypto-trading-license | 34,517 | 34.7 | ✅ → /dubai-crypto-license/ |
| /crypto-license-poland | 33,650 | 54.4 | ✅ → /poland-crypto-license/ |
| /post/securing-your-crypto-license-in-estonia | 22,361 | 65.3 | ✅ → /estonia-crypto-license/ |
| /crypto-license-in-singapore | 21,752 | 45.7 | ✅ added 6/15 → /singapore-crypto-license/ |
| /crypto-license-canada | 15,379 | 29.9 | ✅ added 6/15 → /canada-crypto-license/ |
| /msb-license-canada | 9,671 | 50.6 | ✅ added 6/15 → /canada-crypto-license/ |
| /mas-cryptocurrency-license-singapore | 2,889 | 27.5 | ✅ added 6/15 → /singapore-crypto-license/ |
| /crypto-license-malta | (281 internal + ext links) | — | ✅ added 6/15 → /malta-crypto-license/ |

Net: 57 redirects now funnel ~120K impressions of legacy authority to the live canonical pages.

### CTR opportunity — flagship terms parked on page 1 with 0 clicks
| Query | Impr | Pos | CTR | Action |
|---|---:|---:|---|---|
| panama crypto license | 4,931 | 9.8 | 0% | homepage title/snippet rework + push to top 5 |
| vara license cost | 147 | 9.1 | 1.4% | /dubai or /vara page already p1 — tune snippet |
| crypto license canada | 3,566 | 27.6 | 0% | legacy→/canada redirect (done) should lift it |
| crypto license | 2,263 | 49.2 | 0% | head term; needs authority, long game |

### Remaining plan (performance)
- **P0 CTR:** the homepage ranks ~p10–16 for "panama crypto license" (4.9K impr) yet gets ~0 clicks — rewrite the `<title>`/meta to be more clickable and add a date/price hook; this converts existing impressions without new rankings.
- **P1 authority (the real ceiling):** 369 backlinks won't rank head terms. Earned links / digital PR / the Blogger+satellite network are the lever — this is manual and outside what automation can do.
- **P1 internal links:** Google still shows legacy URLs (`/crypto-license-malta` 281 internal links) in the link graph — recrawl after redirects will repoint equity to canonical pages.

## How to reproduce / re-run

```
python3 scripts/redirects.py          # regenerate redirect stubs from config/redirects.json
python3 scripts/backfill_seo_fixes.py --apply   # repair already-published pages
python3 scripts/publish.py            # rebuild sitemap + IndexNow ping
```
