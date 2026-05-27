# consulting24.co — 1,000-Keyword SEO Build Plan

Goal: publish ~1,000 unique, QC-passing pages (crypto-licensing consulting),
fully cross-linked, indexed in Google + Bing/Yandex + discoverable by LLMs.
Stack: **DataForSEO** (keyword selection) → **Claude** (brain: structure, QC spec,
assembly) → **DeepSeek** (writes) → **QC gate** (rejects under-spec) → publish.

## 1. Keyword architecture (how we reach ~1,000)
Build in topical silos. Use `scripts/keywords.py ideas/volume` to source + validate
volume for every candidate; drop zero-volume / irrelevant terms ("crypto license plate").

| Cluster | Pattern | ~Count |
|---|---|---|
| Jurisdiction money pages | `/[country]-crypto-license/` | ~80 |
| Activity × jurisdiction | `/crypto-[exchange|wallet|broker|otc|fund|nft|payment]-license-[country]/` | ~350 |
| Regulatory/term pages | VASP, CASP, MiCA, VARA, MSB, DASP, EMI, DLT… | ~40 |
| Activity (generic) | exchange, custody, gambling, trading, stablecoin, token-issuance | ~25 |
| Modifier / decision | cost, cheapest, fastest, easiest, best-country, how-to, ready-made, offshore (× key jurisdictions) | ~120 |
| Comparison pages | `/[A]-vs-[B]-crypto-license/` (curated high-intent pairs) | ~120 |
| Blog / informational (support) | educational long-tail feeding the money pages | ~300 |
| **Total** | | **~1,035** |

Process: weekly, run DataForSEO on each cluster's seeds → append validated terms to
`pages.md` / `blog/topics.md` with volume noted → pipeline consumes top-down.

## 2. Crosslinking model (silo + hub-and-spoke — the "link authority flow")
Rules enforced for every page (per QC checklist): ≥1 homepage link, 5–15 internal
links, no orphan pages.
- **Hub:** `/jurisdictions/` links every jurisdiction page (auto-appended).
- **Jurisdiction page →** hub + Panama(home) + 3–4 regional siblings + its activity×jurisdiction children + 1–2 comparisons + 2–3 supporting blogs.
- **Activity×jurisdiction →** parent jurisdiction page + parent activity page + hub.
- **Activity (generic) →** the jurisdictions that offer it + hub.
- **Comparison →** both jurisdiction pages + hub.
- **Blog →** 2–3 relevant money pages + related blogs.
- **Reverse links:** when publishing new pages, add a contextual link from 1–2 closely-related existing pages (no orphans, distributes authority).
- **Tooling to build:** `scripts/linkcheck.py` — crawls all pages, reports orphans, pages with <5 internal links, and broken links; run in the daily task before commit.

## 3. QC compliance at scale (the 25-point checklist)
`scripts/generate.py` already gates: ≥2,300 words, ≥8 FAQs, title 50–65, desc 110–160,
allow-listed internal links, validated external authority links, Service+FAQ+Breadcrumb schema, advisor card.
**To add to the gate for full compliance:**
- [ ] ≥3 images with alt text + optimized filenames (**needs image-source decision**).
- [ ] ≥1 homepage link + 5–15 internal links assertion.
- [ ] keyword in H1 / first 100 words / a H2 / title / meta / URL (auto-check).
- [ ] keyword density 0.8–1.8% (auto-check, reject stuffing).
- [ ] uniqueness ≥85% — unique intro + meta per page (no duplicate templates); spot-check via shingle comparison across the corpus.
- [ ] content mix ~70% educational / 20% commercial / 10% CTA (blog vs landing ratio handles this).
- Freshness: re-generate/refresh pages every 3–6 months (regulations + pricing).

## 4. Cadence & timeline
- Current: 10 landing + 5 blog = **15/day**. → ~1,000 pages in **~67 days**.
- Optional ramp to 20–25/day after Google shows healthy indexing (no manual actions).
- **Risk control (Google "scaled content abuse"):** ramp gradually, keep every page genuinely useful + unique, monitor Search Console for indexing/manual-action warnings, prune or merge any thin/low-performers. Quality gate is the safeguard — never publish below standard.

## 5. Indexing & distribution
- `sitemap.xml` auto-regenerated each run; **IndexNow** ping (Bing/Yandex) instant.
- **Google Search Console:** verify property (tag live) + submit sitemap once; monitor coverage.
- `llms.txt` updated each run; robots.txt allows all AI crawlers (GPTBot/ClaudeBot/Perplexity/etc.).
- Internal links + hub accelerate Google crawl/discovery.

## 6. Build order (next steps)
1. Decide image source (royalty-free per page / branded SVG / generated) → wire into generate.py so QC can require ≥3 images.
2. Extend QC gate (images, homepage link, keyword placement/density, uniqueness).
3. Build `scripts/linkcheck.py` (orphans / <5 links / broken) into the daily task.
4. Backfill the existing 10 short landing pages through DeepSeek to 2,000+.
5. Bulk-expand `pages.md` to the full ~1,000 via DataForSEO cluster sourcing.
6. Let the daily pipeline run; review GSC weekly; ramp cadence if healthy.
