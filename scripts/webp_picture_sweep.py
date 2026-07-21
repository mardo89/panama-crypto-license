#!/usr/bin/env python3
"""Wrap on-page <img src="/img/X.jpg"> in <picture> with a WebP source + JPEG fallback,
where img/X.webp exists. Serves WebP to modern browsers (smaller LCP/weight), JPEG to the
rest. og:image/twitter:image stay JPEG (they're <meta>, untouched). Idempotent.
Usage: python3 scripts/webp_picture_sweep.py [--dry-run]"""
import glob, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HAS_WEBP = {os.path.basename(w)[:-5] for w in glob.glob(os.path.join(ROOT, "img", "*.webp"))}
IMG_RE = re.compile(r'<img\b[^>]*?\bsrc="/img/([a-z0-9-]+)\.jpg"[^>]*?>', re.I)

def wrap(h):
    out, i, n = [], 0, 0
    for m in IMG_RE.finditer(h):
        name = m.group(1)
        if name not in HAS_WEBP:
            continue
        if 'image/webp' in h[max(0, m.start()-90):m.start()]:   # already wrapped
            continue
        out.append(h[i:m.start()])
        out.append(f'<picture><source srcset="/img/{name}.webp" type="image/webp">{m.group(0)}</picture>')
        i = m.end(); n += 1
    out.append(h[i:])
    return "".join(out), n

def main():
    dry = "--dry-run" in sys.argv
    pages = imgs = 0
    for f in glob.glob(os.path.join(ROOT, "**", "index.html"), recursive=True):
        h = open(f, encoding="utf-8").read()
        if 'generated-redirect-stub' in h or 'content="noindex"' in h:
            continue
        nh, n = wrap(h)
        if n:
            imgs += n; pages += 1
            if not dry:
                open(f, "w", encoding="utf-8").write(nh)
    print(f"{'[dry] ' if dry else ''}wrapped {imgs} <img> in <picture> across {pages} pages")

if __name__ == "__main__":
    main()
