#!/usr/bin/env python3
"""
linkcheck.py — internal link-graph audit for consulting24.co.
Reports: broken internal links, pages with <5 internal outbound links, and
orphan pages (no inbound contextual link beyond the global nav/footer).
Run before each daily commit so the link authority graph stays healthy.

  python3 scripts/linkcheck.py
Exit code 1 if broken links found.
"""
import os, re, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def url_for(path):
    rel = os.path.relpath(path, ROOT)
    return "/" if rel == "index.html" else "/" + os.path.dirname(rel) + "/"

pages = {}  # url -> html
for p in glob.glob(os.path.join(ROOT, "**", "index.html"), recursive=True):
    pages[url_for(p)] = open(p, encoding="utf-8").read()

def exists(u):
    u = u.split("#")[0].split("?")[0]
    if not u.startswith("/"): return True
    if u in pages: return True
    # file like /robots.txt, /sitemap.xml, /img/x.svg
    fp = os.path.join(ROOT, u.lstrip("/"))
    return os.path.exists(fp) or os.path.isdir(fp.rstrip("/"))

# global links present on (almost) every page = nav/footer; ignore for orphan calc
counts = collections.Counter()
for url, html in pages.items():
    for h in set(re.findall(r'href="(/[^"#?]*)"', html)):
        counts[h] += 1
GLOBAL = {u for u, c in counts.items() if c >= max(3, int(len(pages) * 0.6))}

broken, thin, orphans = [], [], []
inbound = collections.Counter()
for url, html in pages.items():
    hrefs = re.findall(r'href="(/[^"]*)"', html)
    internal = set(h for h in hrefs if h.startswith("/"))
    if len(internal) < 5:
        thin.append((url, len(internal)))
    for h in internal:
        if not exists(h): broken.append((url, h))
        tgt = h.split("#")[0].split("?")[0]
        if tgt in pages and tgt != url and h not in GLOBAL:
            inbound[tgt] += 1
for url in pages:
    if url == "/" or url in GLOBAL: continue  # globally nav/footer-linked = reachable
    if inbound[url] == 0:
        orphans.append(url)

print(f"pages: {len(pages)} | global nav/footer links: {len(GLOBAL)}")
print(f"\nBROKEN internal links: {len(broken)}")
for src, h in broken[:50]: print(f"  {src}  ->  {h}")
print(f"\nThin pages (<5 internal links): {len(thin)}")
for u, n in thin[:50]: print(f"  {u}  ({n})")
print(f"\nOrphan pages (no contextual inbound link): {len(orphans)}")
for u in orphans[:50]: print(f"  {u}")

import sys
sys.exit(1 if broken else 0)
