#!/usr/bin/env python3
"""One-time on-page sweep for existing pages (the generator handles future pages):
  - meta descriptions: de-truncate to a complete sentence <=155, strip trailing '…'
    across <meta description>, og:description, the on-page 'Short answer' box, and
    Article JSON-LD description (fixes the 380 truncated + the double-escaped box).
  - titles: trim rendered length >65 to <=60 at a word boundary across <title>,
    og:title, twitter:title, JSON-LD headline; add a ' - Consulting24' tail where it fits.
  - related-jurisdiction anchors: descriptive partial-match text + drop the identical
    'Crypto licensing guide and Panama comparison' subtitle repeated ~921x.

Idempotent. Usage: python3 scripts/onpage_sweep.py [--dry-run]
"""
from __future__ import annotations
import glob, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def full_unescape(s):
    for _ in range(4):
        u = html.unescape(s)
        if u == s: return s
        s = u
    return s

def tidy_desc(s):
    s = re.sub(r"\s*(?:\.{2,}|…)+\s*$", "", (s or "").strip()).strip()
    if len(s) <= 158 and s[-1:] in ".!?":
        return s
    cut = s[:156].rstrip()
    ends = [m.end() - 1 for m in re.finditer(r"[.!?]", cut)]
    if ends and ends[-1] >= 90:
        return cut[:ends[-1] + 1].strip()
    commas = [i for i, c in enumerate(cut) if c == "," and i >= 60]
    base = cut[:commas[-1]] if commas else cut.rsplit(" ", 1)[0]
    return base.rstrip(" ,;:-") + "."

def trim_title(t):
    t = t.strip()
    if len(t) <= 60:
        # brand tail where it clearly fits and none present
        if len(t) <= 44 and "Consulting24" not in t:
            return t.rstrip(" -|") + " - Consulting24"
        return t
    t = t[:60].rsplit(" ", 1)[0].rstrip(" -|:&")
    return t

def is_stub(h): return "generated-redirect-stub" in h or 'content="noindex"' in h

def fix_file(f, dry):
    h = open(f, encoding="utf-8").read()
    if is_stub(h): return 0
    orig = h
    changes = 0

    # ---- meta description surfaces ----
    m = re.search(r'<meta name="description" content="(.*?)"', h, re.S)
    if m:
        plain = full_unescape(m.group(1))
        new = tidy_desc(plain)
        if new != plain:
            changes += 1
            new_esc = html.escape(new, quote=True)
            # <meta name=description> and og:description (single-escaped)
            h = re.sub(r'(<meta name="description" content=")(.*?)(")',
                       lambda x: x.group(1) + new_esc + x.group(3), h, count=1, flags=re.S)
            h = re.sub(r'(<meta property="og:description" content=")(.*?)(")',
                       lambda x: x.group(1) + new_esc + x.group(3), h, count=1, flags=re.S)
            # on-page 'Short answer' box (may be double-escaped)
            h = re.sub(r'(Short answer:</strong>\s*)(.*?)(</div>)',
                       lambda x: x.group(1) + new_esc + x.group(3), h, count=1, flags=re.S)
            # Article JSON-LD description (note: may be `"description": "` with a space,
            # and may carry html entities like &#x27; — full_unescape normalizes)
            def _json_desc(x):
                try: raw = json.loads('"' + x.group(2) + '"')
                except Exception: return x.group(0)
                plain = full_unescape(raw)
                fixed = tidy_desc(plain)
                if fixed == plain: return x.group(0)
                return x.group(1) + json.dumps(fixed)[1:-1] + x.group(3)
            h = re.sub(r'("description":\s*")((?:[^"\\]|\\.)*)(")', _json_desc, h)

    # ---- title surfaces ----
    mt = re.search(r'<title>(.*?)</title>', h, re.S)
    if mt:
        plain = full_unescape(mt.group(1))
        new = trim_title(plain)
        if new != plain:
            changes += 1
            new_esc = html.escape(new, quote=True)
            h = h.replace(f'<title>{mt.group(1)}</title>', f'<title>{new_esc}</title>')
            h = re.sub(r'(<meta property="og:title" content=")(.*?)(")',
                       lambda x: x.group(1) + new_esc + x.group(3), h, count=1, flags=re.S)
            h = re.sub(r'(<meta name="twitter:title" content=")(.*?)(")',
                       lambda x: x.group(1) + new_esc + x.group(3), h, count=1, flags=re.S)
            def _json_head(x):
                try: raw = json.loads('"' + x.group(2) + '"')
                except Exception: return x.group(0)
                plain = full_unescape(raw)
                fixed = trim_title(plain)
                if fixed == plain: return x.group(0)
                return x.group(1) + json.dumps(fixed)[1:-1] + x.group(3)
            h = re.sub(r'("headline":\s*")((?:[^"\\]|\\.)*)(")', _json_head, h)

    # ---- related-jurisdiction anchors (descriptive + drop repetitive subtitle) ----
    if "Crypto licensing guide and Panama comparison" in h:
        changes += 1
        # add ' crypto license' to the bold anchor when the name has no parenthetical
        h = re.sub(r'(<a href="[^"]*"><strong>)([^<(]+?)(</strong><span>)Crypto licensing guide and Panama comparison(</span></a>)',
                   r'\1\2 crypto license\3Requirements, cost &amp; timeline\4', h)
        # any remaining (e.g. the 'Panama (EUR 6,000)' card) — just fix the subtitle
        h = h.replace("Crypto licensing guide and Panama comparison", "Requirements, cost &amp; timeline")

    if h != orig and not dry:
        open(f, "w", encoding="utf-8").write(h)
    return 1 if h != orig else 0

def main():
    dry = "--dry-run" in sys.argv
    files = [f for f in glob.glob(os.path.join(ROOT, "**/index.html"), recursive=True)
             if "/node_modules/" not in f]
    changed = 0
    for f in files:
        changed += fix_file(f, dry)
    print(f"{'[dry] ' if dry else ''}pages changed: {changed} / {len(files)}")

if __name__ == "__main__":
    main()
