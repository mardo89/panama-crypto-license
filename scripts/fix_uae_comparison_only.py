#!/usr/bin/env python3
"""SEO audit 2026-07 follow-up: enforce the UAE comparison-only rule on already-
generated pages.

Business rule (user directive 2026-05-27): Consulting24 covers UAE VARA / ADGM
for COMPARISON ONLY and must never claim it advises+coordinates or files a UAE
licence. The generator's COMPARISON_ONLY guard missed compound slugs
(fastest-crypto-license-dubai, vara-license, ...), so ~38 live UAE-family pages
assert "Consulting24 advises and coordinates" a VARA/ADGM application.

This does a DETERMINISTIC, reviewable surgical fix rather than a risky mass
regeneration: any sentence that claims Consulting24 both *advises* AND
*coordinates* a UAE licence is replaced with a single clean comparison-only
sentence. Requiring BOTH tokens targets exactly the violation and leaves the
approved "advises on Dubai as a comparison-only jurisdiction" framing alone.

Run:  python3 scripts/fix_uae_comparison_only.py [--dry-run]
"""
from __future__ import annotations
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRY = "--dry-run" in sys.argv

UAE_DIR = re.compile(r"(dubai|abu-dhabi|vara|uae|adgm)")

def jur_for(text: str, slug: str) -> tuple[str, str]:
    """(display name, 'do not file X applications' keyword) from the sentence,
    falling back to the page slug."""
    t = text.lower()
    if "abu dhabi" in t or "adgm" in t or "fsra" in t:
        return "Abu Dhabi", "ADGM"
    if "dubai" in t or "vara" in t:
        return "Dubai", "VARA"
    if "uae" in t:
        return "the UAE", "UAE"
    # fall back to slug
    if "abu-dhabi" in slug:
        return "Abu Dhabi", "ADGM"
    if "uae" in slug:
        return "the UAE", "UAE"
    return "Dubai", "VARA"

def canonical(name: str, file_kw: str) -> str:
    return (f"Consulting24 covers {name} for comparison only — we do not file "
            f"{file_kw} applications and deliver licenses directly in Panama, "
            f"Estonia, and Lithuania.")

# A "sentence" = a run with no tag/quote delimiters, starting at a capital and
# ending at a period — so a match can never cross an HTML tag or a JSON string
# boundary. We only rewrite it when it claims BOTH advise and coordinate.
SENT = re.compile(r'[A-Z][^.<>"]{0,400}?\.(?=\s|<|"|$)')
STANDALONE = re.compile(r'Consulting24 advises and coordinates\.(?!\w)')

def fix_html(html: str, slug: str) -> tuple[str, int]:
    n = 0
    # 1) the short standalone claim (meta description, og:description, short body)
    def _short(m):
        nonlocal n
        name, _ = jur_for("", slug)
        n += 1
        return f"Consulting24 covers {name} for comparison only."
    html = STANDALONE.sub(_short, html)

    # 2) full sentences asserting advise AND coordinate
    def _sent(m):
        nonlocal n
        s = m.group(0)
        if re.search(r"advis", s, re.I) and re.search(r"coordinat", s, re.I):
            name, kw = jur_for(s, slug)
            n += 1
            return canonical(name, kw)
        return s
    html = SENT.sub(_sent, html)

    # 3) collapse immediate duplicate canonical sentences ("... Lithuania. Consulting24 covers ...")
    dup = re.compile(r"(Consulting24 covers [^.]+? deliver licenses directly in Panama, Estonia, and Lithuania\.)(\s*)\1")
    while dup.search(html):
        html = dup.sub(r"\1", html)
    return html, n

def main():
    total_files = total_edits = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "*", "index.html"))):
        slug = os.path.basename(os.path.dirname(path))
        if not UAE_DIR.search(slug):
            continue
        html = open(path, encoding="utf-8").read()
        new, n = fix_html(html, slug)
        if n:
            total_files += 1
            total_edits += n
            print(f"{'[dry] ' if DRY else ''}{n:3d}  {slug}")
            if not DRY:
                open(path, "w", encoding="utf-8").write(new)
    print(f"\n{total_edits} sentences rewritten across {total_files} UAE-family pages"
          f"{' (dry run)' if DRY else ''}")

if __name__ == "__main__":
    main()
