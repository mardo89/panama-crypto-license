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
import glob, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# redirect stubs are valid pages on disk but noindex; never link INTO them (equity leak +
# redirect hop). Resolve any stub target to its final canonical URL via config/redirects.json.
_RD = {}
try:
    _rj = json.load(open(os.path.join(ROOT, "config", "redirects.json")))["redirects"]
    def _n(p): return "/" + p.strip("/") + "/" if p.strip("/") else "/"
    _RD = {_n(k): (v if v == "/" else _n(v)) for k, v in _rj.items()}
except Exception:
    _RD = {}

def resolve_href(href):
    seen = set()
    for _ in range(5):
        if href in seen or href not in _RD: break
        seen.add(href); href = _RD[href]
    return href
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

# build the index once. DIRS = all page dirs; STUBS = the noindex redirect ones.
DIRS, STUBS = {}, set()
for d in glob.glob(os.path.join(ROOT, "*")):
    if not os.path.isdir(d): continue
    slug = os.path.basename(d)
    idx = os.path.join(d, "index.html")
    if os.path.exists(idx):
        DIRS[slug] = True
        head = open(idx, encoding="utf-8").read(400)
        if "generated-redirect-stub" in head or 'content="noindex"' in head:
            STUBS.add(slug)
by_country, by_activity = {}, {}
for slug in DIRS:
    if slug in STUBS: continue          # never offer a stub as a sibling link target
    a, c = parse(slug)
    if a:
        by_country.setdefault(c, []).append((a, slug))
        by_activity.setdefault(a, []).append((c, slug))

def _ring(group, slug, n=3):
    """Pick n siblings starting AFTER this page's position in the sorted group and wrapping
    around. Every member is then linked by the n members preceding it in the ring, so no tail
    entry (e.g. an alphabetically-last country like Vietnam) is left without inbound links,
    which a plain sorted[:n] slice would strand."""
    ordered = [x for x in sorted(group)]              # (key, slug) tuples
    slugs = [s for _, s in ordered]
    if slug not in slugs: return []
    i = slugs.index(slug)
    N = len(ordered)
    out = []
    for k in range(1, N):
        if len(out) >= n: break
        out.append(ordered[(i + k) % N])
    return out

def block_for(slug):
    a, c = parse(slug)
    if not a: return None
    links = []
    if f"{c}-crypto-license" in DIRS:
        # resolve the country hub through redirects (e.g. /panama-crypto-license/ is a stub -> /)
        links.append((resolve_href(f"/{c}-crypto-license/"), f"{cap(c)} crypto license"))
    for aa, s in _ring(by_country.get(c, []), slug):
        links.append((f"/{s}/", f"{cap(c)} {act_label(aa)} license"))
    for cc, s in _ring(by_activity.get(a, []), slug):
        links.append((f"/{s}/", f"{cap(cc)} {act_label(a)} license"))
    links.append(("/", "Panama (EUR 6,000)"))
    seen, uniq = set(), []
    for href, label in links:
        if href in seen: continue
        seen.add(href); uniq.append((href, label))
    items = "".join(f'<a href="{href}">{html.escape(label)}</a>' for href, label in uniq)
    return f'<section class="reciprocal related"><h2>Related crypto licenses</h2><div class="related">{items}</div></section>'

_BLOCK_RE = re.compile(r'<section class="reciprocal related">.*?</section>\n?', re.S)

def fix(path, dry):
    slug = os.path.basename(os.path.dirname(path))
    a, c = parse(slug)
    if not a: return False
    h = open(path, encoding="utf-8").read()
    if is_stub(h): return False
    blk = block_for(slug)
    if not blk or "</article>" not in h: return False
    # re-injectable: strip any prior block so an improved ring layout replaces the old slice
    stripped = _BLOCK_RE.sub("", h)
    new = stripped.replace("</article>", blk + "\n</article>", 1)
    if new == h: return False
    if not dry: open(path, "w", encoding="utf-8").write(new)
    return True

def main():
    dry = "--dry-run" in sys.argv
    files = glob.glob(os.path.join(ROOT, "*", "index.html"))
    n = sum(1 for f in files if fix(f, dry))
    print(f"{'[dry] ' if dry else ''}reciprocal links injected into {n} activity×country pages")

if __name__ == "__main__":
    main()
