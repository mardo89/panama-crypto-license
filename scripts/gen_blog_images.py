#!/usr/bin/env python3
"""
gen_blog_images.py — generate a UNIQUE branded hero image per Blogger post/page.

Problem: _hero_photo cycled 9 gallery photos across 100 items, so images repeated.
Fix: composite a per-item image = (varied gallery photo, darkened) + brand gradient
+ the item's title text + an accent underline (color varied per item) + wordmark.
Every post/page gets a visually distinct 1200x630 JPG at img/blog/<slug>.jpg.

Reads titles from config/blog_posted.json. Idempotent (regenerates only missing
unless --force). Requires Pillow.

Usage:
  python3 scripts/gen_blog_images.py            # generate missing
  python3 scripts/gen_blog_images.py --force    # regenerate all
"""
from __future__ import annotations
import json, pathlib, sys, textwrap, hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT / "config" / "blog_posted.json"
GALLERY = sorted((ROOT / "img").glob("gallery-*.jpg"))
OUTDIR = ROOT / "img" / "blog"
F_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
F_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"

W, H = 1200, 630
# accent palette (brand-ish blues/greens/teal) chosen per item for variety
ACCENTS = [(37,211,102),(17,109,255),(66,165,245),(0,191,165),(124,77,255),
           (255,143,0),(236,64,122),(38,198,218),(102,187,106),(255,202,40)]

def font(path, size):
    return ImageFont.truetype(path, size)

def hkey(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest(), 16)

def make_image(slug: str, title: str) -> Image.Image:
    h = hkey(slug)
    base_path = GALLERY[h % len(GALLERY)]
    accent = ACCENTS[(h >> 8) % len(ACCENTS)]
    # 1) base photo cropped to cover 1200x630
    img = Image.open(base_path).convert("RGB")
    bw, bh = img.size
    scale = max(W / bw, H / bh)
    img = img.resize((int(bw * scale) + 1, int(bh * scale) + 1))
    img = img.crop((0, 0, W, H))
    # slight blur so text reads clearly
    img = img.filter(ImageFilter.GaussianBlur(2))
    # 2) dark gradient overlay (darker on the left where text sits)
    grad = Image.new("L", (W, 1))
    for x in range(W):
        grad.putpixel((x, 0), int(225 - (x / W) * 150))  # 225 -> 75 alpha
    grad = grad.resize((W, H))
    dark = Image.new("RGB", (W, H), (8, 18, 38))
    img = Image.composite(dark, img, grad)
    # extra bottom shade
    bshade = Image.new("L", (1, H))
    for y in range(H):
        bshade.putpixel((0, y), int(max(0, (y - H * 0.55) / (H * 0.45) * 150)))
    bshade = bshade.resize((W, H))
    img = Image.composite(Image.new("RGB", (W, H), (5, 12, 28)), img, bshade)

    d = ImageDraw.Draw(img)
    # 3) eyebrow
    d.text((80, 86), "CRYPTO LICENSE GUIDE  ·  2026",
           font=font(F_BOLD, 26), fill=(207, 230, 255))
    # 4) title (wrapped), size by length
    t = title.strip()
    fs = 70 if len(t) <= 34 else 58 if len(t) <= 52 else 48 if len(t) <= 74 else 40
    tf = font(F_BOLD, fs)
    # wrap to width ~ W-160 px
    avg = tf.getlength("n") or fs * 0.55
    maxchars = max(12, int((W - 160) / (avg)))
    lines = textwrap.wrap(t, width=maxchars)[:4]
    y = 150
    for ln in lines:
        d.text((80, y), ln, font=tf, fill=(255, 255, 255))
        y += int(fs * 1.16)
    # 5) accent underline
    d.rounded_rectangle([82, y + 8, 82 + 150, y + 8 + 8], radius=4, fill=accent)
    # 6) wordmark
    d.ellipse([80, H - 66, 92, H - 54], fill=accent)
    d.text((104, H - 74), "CONSULTING24.CO", font=font(F_BOLD, 24),
           fill=(180, 200, 230))
    return img

def main():
    force = "--force" in sys.argv
    OUTDIR.mkdir(parents=True, exist_ok=True)
    state = json.loads(STATE.read_text())
    items = {}
    for kind in ("posts", "pages"):
        for slug, m in state.get(kind, {}).items():
            if m.get("title"):
                items[slug] = m["title"]
    made = skipped = 0
    for slug, title in items.items():
        out = OUTDIR / f"{slug}.jpg"
        if out.exists() and not force:
            skipped += 1; continue
        try:
            im = make_image(slug, title)
            im.save(out, "JPEG", quality=82, optimize=True)
            made += 1
        except Exception as e:
            print(f"ERROR {slug}: {e}")
    print(f"blog images: {made} generated, {skipped} existing ({len(items)} items, "
          f"{len(GALLERY)} base photos)")

if __name__ == "__main__":
    main()
