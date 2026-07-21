#!/usr/bin/env python3
"""Link every published Blogger post & page from the consulting24.co website.

The Blogger feeder blog (blog.consulting24.co) links TO the consulting24.co money
pages; this script does the reverse — it keeps a complete, auto-generated list of
ALL Blogger guides on the site's /blog/ hub so every blog URL is linked from the
main site. Run daily after the Blogger poster.

- Source of truth: config/blog_posted.json  (posts + pages, written by consulting24_blog.py)
- Target: blog/index.html, between <!-- BLOGGER_GUIDES_START --> and <!-- BLOGGER_GUIDES_END -->
- Idempotent: regenerates the full block each run (so newly published items get linked).

Usage:
  python3 scripts/link_blogger.py            # update the block
  python3 scripts/link_blogger.py --check    # exit 1 if the block is out of date (no write)
"""
from __future__ import annotations
import json, pathlib, sys, html, re

ROOT   = pathlib.Path(__file__).resolve().parents[1]
STATE  = ROOT / "config" / "blog_posted.json"
TARGET = ROOT / "blog" / "index.html"
START  = "<!-- BLOGGER_GUIDES_START -->"
END    = "<!-- BLOGGER_GUIDES_END -->"

def load_items() -> list[dict]:
    data = json.loads(STATE.read_text()) if STATE.exists() else {}
    items = []
    for kind in ("pages", "posts"):                 # pillar pages first, then posts
        for slug, m in data.get(kind, {}).items():
            if m.get("url") and m.get("title"):
                items.append({"title": m["title"], "url": m["url"],
                              "kind": "Pillar guide" if kind == "pages" else "Guide"})
    return items

def render_block(items: list[dict]) -> str:
    if not items:
        cards = "<p>Guides coming soon.</p>"
    else:
        def _thumb(title: str) -> int:
            return (sum(ord(c) for c in title) % 9) + 1
        cards = "".join(
            f'<a class="post-card" href="{html.escape(i["url"])}" '
            f'rel="noopener">'
            f'<picture><source srcset="/img/gallery-{_thumb(i["title"]):02d}.webp" type="image/webp">'
            f'<img class="thumb" src="/img/gallery-{_thumb(i["title"]):02d}.jpg" '
            f'alt="{html.escape(i["title"])}" loading="lazy" width="600" height="360"></picture>'
            f'<span class="pc-body"><span class="cat">{i["kind"]}</span>'
            f'<h2>{html.escape(i["title"])}</h2>'
            f'<span class="meta">Consulting24 blog</span></span></a>'
            for i in items
        )
        cards = f'<div class="blog-grid">{cards}</div>'
    return f"{START}\n  {cards}\n  {END}"

def main():
    check = "--check" in sys.argv
    items = load_items()
    htmltext = TARGET.read_text()
    if START not in htmltext or END not in htmltext:
        sys.exit(f"ERROR: markers not found in {TARGET}")
    new_block = render_block(items)
    updated = re.sub(re.escape(START) + r".*?" + re.escape(END), new_block,
                     htmltext, flags=re.S)
    if updated == htmltext:
        print(f"link_blogger: up to date ({len(items)} guides linked).")
        return
    if check:
        print(f"link_blogger: OUT OF DATE — {len(items)} guides should be linked.")
        sys.exit(1)
    TARGET.write_text(updated)
    print(f"link_blogger: linked {len(items)} Blogger guides into {TARGET.relative_to(ROOT)}.")

if __name__ == "__main__":
    main()
