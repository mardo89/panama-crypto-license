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

# --- Jurisdictions hub: every root-level *-crypto-license page + Panama ---
cards = ['    <a class="jx-card" href="/"><strong>Panama 🇵🇦</strong><span>€6,000 fixed · 2–3 weeks · 0% foreign-income tax</span></a>']
for d in sorted(glob.glob(os.path.join(ROOT, "*-crypto-license"))):
    slug = os.path.basename(d)
    if not os.path.exists(os.path.join(d, "index.html")): continue
    name = slug.replace("-crypto-license", "").replace("-", " ").title()
    cards.append(f'    <a class="jx-card" href="/{slug}/"><strong>{name}</strong><span>Crypto licensing guide &amp; Panama comparison</span></a>')
hub_block = '  <div class="jx-grid">\n' + "\n".join(cards) + "\n  </div>"
splice(os.path.join(ROOT, "jurisdictions", "index.html"), "<!-- JURISDICTIONS_START -->", "<!-- JURISDICTIONS_END -->", hub_block)
print(f"hub: {len(cards)} jurisdiction cards")

# --- Blog index: every blog/<slug>/ post, newest (by mtime) first ---
posts = []
for d in glob.glob(os.path.join(ROOT, "blog", "*")):
    idx = os.path.join(d, "index.html")
    if os.path.isdir(d) and os.path.exists(idx):
        posts.append((os.path.getmtime(idx), os.path.basename(d), idx))
posts.sort(reverse=True)
bcards = []
for _, slug, idx in posts:
    t = title_of(idx, slug)
    bcards.append(f'    <a class="post-card" href="/blog/{slug}/"><span class="cat">Guide</span><h3>{t}</h3><span class="meta">Consulting24</span></a>')
blog_block = '  <div class="blog-grid">\n' + "\n".join(bcards) + "\n  </div>"
splice(os.path.join(ROOT, "blog", "index.html"), "<!-- BLOG_POSTS_START -->", "<!-- BLOG_POSTS_END -->", blog_block)
print(f"blog index: {len(bcards)} post cards")
