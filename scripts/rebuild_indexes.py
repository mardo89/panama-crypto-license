#!/usr/bin/env python3
"""
rebuild_indexes.py — regenerate the /jurisdictions/ hub grid and /blog/ card list
from whatever pages exist on disk, so new pages are always linked (no orphans).
Run in the daily pipeline after generating pages, before linkcheck/publish.
"""
import os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def title_of(path, fallback):
    h = open(path, encoding="utf-8").read()
    m = re.search(r"<h1>(.*?)</h1>", h, re.S)
    t = re.sub("<[^>]+>", "", m.group(1)).strip() if m else fallback
    return t

def splice(file, start, end, block):
    s = open(file, encoding="utf-8").read()
    new = re.sub(re.escape(start) + r".*?" + re.escape(end), start + "\n" + block + "\n" + end, s, flags=re.S)
    open(file, "w", encoding="utf-8").write(new)

# --- Jurisdictions hub: link EVERY indexable landing page, grouped, so no page is
#     an orphan. Runs on every publish, so new pages are auto-wired in. ---
SYSTEM = {"blog","scripts","config","img","logs","jurisdictions","node_modules",
          "about","contact","privacy","terms","cookies","post"}
ACT = ("exchange","broker","fund","gambling","nft-marketplace","otc-desk","payment-institution",
       "stablecoin","staking","token-issuance","wallet-custody","dealer","custody","mining","p2p")

def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def classify(slug):
    if "-vs-" in slug: return "compare"
    if slug.startswith(("best-country","cost-crypto","offshore-crypto","fastest-crypto",
                        "cheapest-crypto","easiest-crypto","ready-made-crypto","how-to-")):
        return "guide"
    if slug.startswith("crypto-") and any(f"crypto-{a}-license" in slug for a in ACT):
        return "activity"
    if slug.endswith("-crypto-license"): return "jurisdiction"
    return "guide"

groups = {"jurisdiction": [], "activity": [], "compare": [], "guide": []}
for d in sorted(glob.glob(os.path.join(ROOT, "*"))):
    if not os.path.isdir(d): continue
    slug = os.path.basename(d)
    idx = os.path.join(d, "index.html")
    if slug in SYSTEM or slug.startswith(".") or not os.path.exists(idx): continue
    h = open(idx, encoding="utf-8").read()
    if 'generated-redirect-stub' in h or 'content="noindex"' in h: continue   # skip stubs
    label = title_of(idx, slug.replace("-", " ").title())
    groups[classify(slug)].append((label, slug))

SUB = {"jurisdiction":"Requirements, cost &amp; timeline", "activity":"Licence type &amp; process",
       "compare":"Side-by-side comparison", "guide":"Guide"}
HEAD = {"jurisdiction":"Crypto license by country", "activity":"By licence type &amp; activity",
        "compare":"Compare jurisdictions", "guide":"Guides &amp; tools"}
sections = ['  <div class="jx-grid">\n    <a class="jx-card" href="/"><strong>Panama 🇵🇦</strong>'
            '<span>€6,000 fixed · 2–3 weeks · 0% foreign-income tax</span></a>\n  </div>']
total = 1
for key in ("jurisdiction", "activity", "compare", "guide"):
    items = groups[key]
    if not items: continue
    total += len(items)
    cards = "\n".join(
        f'    <a class="jx-card" href="/{slug}/"><strong>{esc(label)}</strong><span>{SUB[key]}</span></a>'
        for label, slug in items)
    sections.append(f'  <h2 class="jx-group">{HEAD[key]}</h2>\n  <div class="jx-grid">\n{cards}\n  </div>')
hub_block = "\n".join(sections)
splice(os.path.join(ROOT, "jurisdictions", "index.html"), "<!-- JURISDICTIONS_START -->", "<!-- JURISDICTIONS_END -->", hub_block)
print(f"hub: {total} landing pages linked across {sum(1 for k in groups if groups[k])} groups")

# --- Blog index: every blog/<slug>/ post, newest (by mtime) first ---
posts = []
for d in glob.glob(os.path.join(ROOT, "blog", "*")):
    idx = os.path.join(d, "index.html")
    if os.path.isdir(d) and os.path.exists(idx):
        bh = open(idx, encoding="utf-8").read()
        if 'generated-redirect-stub' in bh or 'content="noindex"' in bh:
            continue                      # skip redirect stubs (deduped comparison posts)
        posts.append((os.path.getmtime(idx), os.path.basename(d), idx))
posts.sort(reverse=True)
bcards = []
for _, slug, idx in posts:
    t = title_of(idx, slug)
    gi = (sum(ord(c) for c in slug) % 9) + 1   # matches the post's hero photo
    bcards.append(
        f'    <a class="post-card" href="/blog/{slug}/">'
        f'<img class="thumb" src="/img/gallery-{gi:02d}.jpg" alt="{t}" loading="lazy" width="600" height="360">'
        f'<span class="pc-body"><span class="cat">Guide</span><h3>{t}</h3>'
        f'<span class="meta">Consulting24</span></span></a>')
blog_block = '  <div class="blog-grid">\n' + "\n".join(bcards) + "\n  </div>"
splice(os.path.join(ROOT, "blog", "index.html"), "<!-- BLOG_POSTS_START -->", "<!-- BLOG_POSTS_END -->", blog_block)
print(f"blog index: {len(bcards)} post cards")
