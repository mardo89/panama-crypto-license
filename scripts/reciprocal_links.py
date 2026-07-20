#!/usr/bin/env python3
"""Give every activity×country landing page in-body contextual links to its siblings,
so ~474 pages that were reachable only from the /jurisdictions/ hub earn real in-prose
inbound links (fixes linkcheck's 'contextual orphan' cluster and tightens the silo).

For /crypto-{activity}-license-{country}/ each page links:
  - its country hub /{country}-crypto-license/ (if it exists),
  - up to 3 same-country pages (other activities),
  - up to 3 same-activity pages (other countries),
  - Panama (the money route).
Injected once, idempotently, right before </article>.

Idempotent. Usage: python3 scripts/reciprocal_links.py [--dry-run]
"""
from __future__ import annotations
import glob, html, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACT = ["exchange", "token-issuance", "payment-institution", "stablecoin", "gambling",
       "nft-marketplace", "fund", "staking", "otc-desk", "wallet-custody", "broker"]
SPECIAL = {"bvi": "BVI", "usa": "USA", "uae": "UAE", "el-salvador": "El Salvador",
           "czech-republic": "Czech Republic", "hong-kong": "Hong Kong", "abu-dhabi": "Abu Dhabi",
           "cayman-islands": "Cayman Islands", "saudi-arabia": "Saudi Arabia", "south-africa": "South Africa",
           "costa-rica": "Costa Rica", "saint-lucia": "Saint Lucia", "new-zealand": "New Zealand"}
ACT_LABEL = {"otc-desk": "OTC desk", "nft-marketplace": "NFT marketplace", "wallet-custody": "wallet & custody",
             "token-issuance": "token issuance", "payment-institution": "payment institution"}

def cap(w): return SPECIAL.get(w, w.replace("-", " ").title())
def act_label(a): return ACT_LABEL.get(a, a.replace("-", " "))

def parse(slug):
    m = re.match(r"^crypto-(" + "|".join(ACT) + r")-license-(.+)$", slug)
    return (m.group(1), m.group(2)) if m else (None, None)

def is_stub(h): return "generated-redirect-stub" in h or 'content="noindex"' in h

# build the index once
DIRS = {}
for d in glob.glob(os.path.join(ROOT, "*")):
    if not os.path.isdir(d): continue
    slug = os.path.basename(d)
    if os.path.exists(os.path.join(d, "index.html")):
        DIRS[slug] = True
by_country, by_activity = {}, {}
for slug in DIRS:
    a, c = parse(slug)
    if a:
        by_country.setdefault(c, []).append((a, slug))
        by_activity.setdefault(a, []).append((c, slug))

def block_for(slug):
    a, c = parse(slug)
    if not a: return None
    links = []
    if f"{c}-crypto-license" in DIRS:
        links.append((f"/{c}-crypto-license/", f"{cap(c)} crypto license"))
    same_country = [(s, aa) for (aa, s) in sorted(by_country.get(c, [])) if s != slug][:3]
    for s, aa in same_country:
        links.append((f"/{s}/", f"{cap(c)} {act_label(aa)} license"))
    same_act = [(s, cc) for (cc, s) in sorted(by_activity.get(a, [])) if s != slug][:3]
    for s, cc in same_act:
        links.append((f"/{s}/", f"{cap(cc)} {act_label(a)} license"))
    links.append(("/", "Panama (EUR 6,000)"))
    seen, uniq = set(), []
    for href, label in links:
        if href in seen: continue
        seen.add(href); uniq.append((href, label))
    items = "".join(f'<a href="{href}">{html.escape(label)}</a>' for href, label in uniq)
    return f'<section class="reciprocal related"><h2>Related crypto licenses</h2><div class="related">{items}</div></section>'

def fix(path, dry):
    slug = os.path.basename(os.path.dirname(path))
    a, c = parse(slug)
    if not a: return False
    h = open(path, encoding="utf-8").read()
    if is_stub(h) or 'class="reciprocal' in h: return False
    blk = block_for(slug)
    if not blk or "</article>" not in h: return False
    h = h.replace("</article>", blk + "\n</article>", 1)
    if not dry: open(path, "w", encoding="utf-8").write(h)
    return True

def main():
    dry = "--dry-run" in sys.argv
    files = glob.glob(os.path.join(ROOT, "*", "index.html"))
    n = sum(1 for f in files if fix(f, dry))
    print(f"{'[dry] ' if dry else ''}reciprocal links injected into {n} activity×country pages")

if __name__ == "__main__":
    main()
