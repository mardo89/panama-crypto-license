#!/usr/bin/env python3
"""
backfill_seo_fixes.py — one-off repair of already-published landing pages.

Fixes three defects left by earlier generator versions, in place (no DeepSeek calls):
  1) Malformed <title>/og:title/Article headline — duplicated keyword junk like
     "Crypto Exchange License Romania Crypto License: Crypto Exchange".
     Rebuilt deterministically from the slug, with correct acronym casing.
  2) Missing "Official sources" block — injected from regulators.sources_block(slug).
  3) Missing Article (author/date) schema — injected before </head>.
  4) Cosmetic: homepage hub link rendered as href="//" -> href="/".

Run from repo root:  python3 scripts/backfill_seo_fixes.py [--apply]
Without --apply it's a dry run (prints what would change).
"""
import os, re, sys, glob, json, datetime, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
try:
    from regulators import sources_block
except Exception:
    def sources_block(slug): return ""

BASE = "https://www.consulting24.co"
SKIP = {"blog", "scripts", "config", "img", "logs", "jurisdictions"}

# ---- casing for slug -> Title phrase -----------------------------------------
ACR = {"nft": "NFT", "otc": "OTC", "mica": "MiCA", "vasp": "VASP", "casp": "CASP",
       "msb": "MSB", "vara": "VARA", "vqf": "VQF", "bvi": "BVI", "usa": "USA",
       "uae": "UAE", "adgm": "ADGM", "dlt": "DLT", "aml": "AML", "kyc": "KYC",
       "ieo": "IEO", "bsp": "BSP", "dasp": "DASP", "psa": "PSA"}
SMALL = {"of", "and", "the", "for", "vs", "in", "to", "a"}

def titlecase(tokens):
    out = []
    for i, w in enumerate(tokens):
        lw = w.lower()
        if lw in ACR:
            out.append(ACR[lw])
        elif lw in SMALL and i != 0:
            out.append(lw)
        else:
            out.append(w[:1].upper() + w[1:].lower())
    return " ".join(out)

# Countries that can appear as a slug suffix (longest match first).
COUNTRIES = [
    "abu-dhabi", "cayman-islands", "costa-rica", "czech-republic", "el-salvador",
    "hong-kong", "isle-of-man", "marshall-islands", "saint-lucia", "saudi-arabia",
    "south-africa", "south-korea", "united-kingdom",
    "anjouan", "bahamas", "bahrain", "belize", "bermuda", "bulgaria", "bvi",
    "canada", "croatia", "cyprus", "dubai", "estonia", "france", "georgia",
    "germany", "gibraltar", "greece", "hungary", "ireland", "italy", "jersey",
    "labuan", "latvia", "liechtenstein", "lithuania", "luxembourg", "malta",
    "mauritius", "netherlands", "panama", "poland", "portugal", "qatar",
    "romania", "seychelles", "singapore", "slovakia", "spain", "switzerland",
    "uae", "usa", "vanuatu",
]
COUNTRIES.sort(key=len, reverse=True)

def clean_title(slug):
    """Deterministic, non-duplicated <=65-char title from a slug."""
    s = slug
    # comparison pages: a-vs-b-crypto-license
    if "-vs-" in s:
        phrase = titlecase(s.replace("-crypto-license", "").split("-"))
        t = f"{phrase} Crypto License: 2026 Comparison"
        return _fit(t)
    # tier-1 jurisdiction money page: <country>-crypto-license
    if s.endswith("-crypto-license") and s.count("-") and not s.startswith("crypto-"):
        country = titlecase(s[:-len("-crypto-license")].split("-"))
        return _fit(f"{country} Crypto License 2026: Cost & Requirements")
    # vertical pages: crypto-<vertical>-license[-<country>]
    if s.startswith("crypto-") and "-license" in s:
        country = None
        for c in COUNTRIES:
            if s.endswith("-" + c):
                country = c
                s_core = s[: -len("-" + c)]
                break
        else:
            s_core = s
        vertical = titlecase(s_core.split("-"))   # e.g. "Crypto Exchange License"
        if country:
            ct = titlecase(country.split("-"))
            return _fit(f"{vertical} in {ct} (2026): Cost & Setup")
        return _fit(f"{vertical} (2026): Cost, Process & Requirements")
    # everything else (cost-/best-country-/how-to- ...): title-case + year
    phrase = titlecase(s.split("-"))
    return _fit(f"{phrase} (2026 Guide)")

def _fit(t):
    if len(t) <= 65:
        return t
    # trim trailing parenthetical / suffix words until it fits
    t = re.sub(r"\s*\([^)]*\)\s*$", "", t)
    if len(t) <= 65:
        return t
    return t[:65].rsplit(" ", 1)[0].rstrip(" .,:;&-—")

def is_malformed(title):
    low = title.lower()
    return low.count("crypto") >= 2 or low.count("license") >= 2 or " nft " in (" "+low+" ") and "NFT" not in title

# ---- per-file repair ---------------------------------------------------------
def process(path, apply):
    slug = os.path.dirname(path).replace(ROOT + os.sep, "").strip(os.sep)
    if slug in SKIP or os.sep in slug:
        return None
    src = open(path, encoding="utf-8").read()
    changed = []
    out = src

    m = re.search(r"<title>(.*?)</title>", out, re.S)
    if m:
        cur = html.unescape(m.group(1)).strip()
        if is_malformed(cur):
            new = clean_title(slug)
            if new and new != cur:
                cur_esc = m.group(1).strip()                 # as it appears (escaped)
                new_esc = html.escape(new)
                # replace the exact escaped string everywhere (title, og:title, headline)
                out = out.replace(cur_esc, new_esc)
                changed.append(f"title: {cur!r} -> {new!r}")

    # inject Official sources if missing
    if "Official sources" not in out:
        blk = sources_block(slug)
        if blk and "<h2>Related jurisdictions</h2>" in out:
            out = out.replace("<h2>Related jurisdictions</h2>",
                              blk + "\n<h2>Related jurisdictions</h2>", 1)
            changed.append("inject: Official sources")

    # inject Article schema if missing
    if '"@type": "Article"' not in out and '"@type":"Article"' not in out:
        td = datetime.date.today().isoformat()
        tm = re.search(r"<title>(.*?)</title>", out, re.S)
        dm = re.search(r'name="description" content="(.*?)"', out, re.S)
        ttl = (tm.group(1).strip() if tm else slug)
        desc = (dm.group(1).strip() if dm else "")
        art = ('<script type="application/ld+json">{"@context":"https://schema.org",'
               '"@type":"Article","headline":%s,"description":%s,'
               '"datePublished":"%s","dateModified":"%s",'
               '"image":"%s/og-image.jpg","mainEntityOfPage":"%s/%s/",'
               '"author":{"@type":"Person","name":"Mardo Soo","jobTitle":"Founder & CEO",'
               '"url":"https://www.linkedin.com/in/mardo-s-00a05ab0/",'
               '"image":"%s/img/mardo-soo-profile.jpg",'
               '"worksFor":{"@type":"Organization","name":"Consulting24","url":"https://consulting24.co/"}},'
               '"publisher":{"@type":"Organization","name":"Consulting24","url":"https://consulting24.co/",'
               '"logo":{"@type":"ImageObject","url":"%s/img/mardo-soo-profile.jpg"}}}</script>'
               % (json.dumps(html.unescape(ttl)), json.dumps(html.unescape(desc)),
                  td, td, BASE, BASE, slug, BASE, BASE))
        if "</head>" in out:
            out = out.replace("</head>", art + "\n</head>", 1)
            changed.append("inject: Article schema")

    # cosmetic: href="//" homepage hub link -> href="/"
    if 'href="//"' in out:
        out = out.replace('href="//"', 'href="/"')
        changed.append('fix: href="//" -> "/"')

    if changed and apply:
        open(path, "w", encoding="utf-8").write(out)
    return (slug, changed) if changed else None


def main():
    apply = "--apply" in sys.argv
    os.chdir(ROOT)
    results = []
    for path in sorted(glob.glob("*/index.html")):
        r = process(os.path.join(ROOT, path), apply)
        if r:
            results.append(r)
    titles = sum(1 for _, c in results if any(x.startswith("title:") for x in c))
    srcs = sum(1 for _, c in results if any("Official sources" in x for x in c))
    arts = sum(1 for _, c in results if any("Article schema" in x for x in c))
    hrefs = sum(1 for _, c in results if any('href=' in x for x in c))
    print(f"{'APPLIED' if apply else 'DRY-RUN'}: {len(results)} pages changed")
    print(f"  titles rebuilt     : {titles}")
    print(f"  sources injected   : {srcs}")
    print(f"  article schema add : {arts}")
    print(f"  href// fixed       : {hrefs}")
    print("--- sample (first 20 title rewrites) ---")
    n = 0
    for slug, c in results:
        for x in c:
            if x.startswith("title:") and n < 20:
                print(f"  [{slug}] {x}")
                n += 1


if __name__ == "__main__":
    main()
