#!/usr/bin/env python3
"""One-time JSON-LD repair for existing pages (generate.py fixed for future pages):
  1. comparison-only (UAE/VARA/ADGM) pages: remove the Service node that falsely claims
     provider=Consulting24 (we do NOT provide those licences).
  2. one canonical Organization (@id, legalName, address, reg nr, sameAs=[blog]) per page;
     Service.provider / Article author.worksFor / publisher all reference it by @id.
     ONLY real profiles in sameAs (blog.consulting24.co) - no fabricated LinkedIn/Medium.
  3. blog posts: BreadcrumbList + visible nav nest under /blog/, not /jurisdictions/.
  4. Article author gets an on-site @id (/about/#mardo-soo) + sameAs [LinkedIn].
  5. the 4 Panama-route money pages gain a priced Service+Offer (EUR 6,000).

Idempotent. Usage: python3 scripts/schema_repair.py [--dry-run]
"""
from __future__ import annotations
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.consulting24.co"
ORG_ID = f"{BASE}/#business"
AUTHOR_ID = f"{BASE}/about/#mardo-soo"
LINKEDIN = "https://www.linkedin.com/in/mardo-s-00a05ab0/"
CO_TOKENS = ("dubai", "abu-dhabi", "uae", "vara", "adgm")
PANAMA_OFFER_PAGES = {"requirements", "application-process", "company-setup", "best-country-crypto-license-panama"}

ORG_NODE = {
    "@type": "Organization", "@id": ORG_ID, "name": "Consulting24", "legalName": "X24Consulting OÜ",
    "url": f"{BASE}/", "logo": {"@type": "ImageObject", "url": f"{BASE}/img/mardo-soo-profile.jpg"},
    "identifier": {"@type": "PropertyValue", "propertyID": "Estonian Business Register", "value": "16971898"},
    "address": {"@type": "PostalAddress", "streetAddress": "Poordi 3-63", "addressLocality": "Tallinn",
                "postalCode": "10156", "addressCountry": "EE"},
    "sameAs": ["https://blog.consulting24.co/"],
}
PANAMA_OFFER = {
    "@type": "Service", "name": "Panama Crypto Company Registration", "provider": {"@id": ORG_ID},
    "areaServed": {"@type": "Country", "name": "Panama"},
    "offers": {"@type": "Offer", "price": "6000", "priceCurrency": "EUR",
               "availability": "https://schema.org/InStock",
               "priceSpecification": {"@type": "UnitPriceSpecification", "price": "6000", "priceCurrency": "EUR"},
               "description": "Fixed-fee Panama crypto company registration; EUR 250 per additional beneficial owner."},
}

def is_stub(h): return "generated-redirect-stub" in h or 'content="noindex"' in h
def graph_of(obj): return obj["@graph"] if isinstance(obj, dict) and "@graph" in obj else ([obj] if isinstance(obj, dict) else obj)

def repair(path):
    slug = os.path.relpath(os.path.dirname(path), ROOT)
    h = open(path, encoding="utf-8").read()
    if is_stub(h): return False
    is_blog = slug.startswith("blog/")
    base_slug = slug.split("/")[-1]
    comparison_only = any(t in base_slug for t in CO_TOKENS)
    blocks = list(re.finditer(r'(<script type="application/ld\+json">)(.*?)(</script>)', h, re.S))
    if not blocks: return False
    new_h, changed = h, False

    for m in blocks:
        try:
            obj = json.loads(m.group(2))
        except Exception:
            continue
        g = graph_of(obj)
        if not isinstance(g, list):
            continue
        types = {n.get("@type") for n in g if isinstance(n, dict)}
        touched = False

        if "BreadcrumbList" in types:
            # canonical Organization node (once)
            if not any(isinstance(n, dict) and n.get("@id") == ORG_ID for n in g):
                g.insert(0, ORG_NODE); touched = True
            # breadcrumb nesting for blog
            for n in g:
                if isinstance(n, dict) and n.get("@type") == "BreadcrumbList":
                    for it in n.get("itemListElement", []):
                        if it.get("position") == 2 and is_blog and it.get("name") != "Blog":
                            it["name"] = "Blog"; it["item"] = f"{BASE}/blog/"; touched = True
            # Service node: drop on comparison-only, else ref org by @id
            keep = []
            for n in g:
                if isinstance(n, dict) and n.get("@type") == "Service":
                    if comparison_only:
                        touched = True; continue          # drop false provider claim
                    if n.get("provider") != {"@id": ORG_ID}:
                        n["provider"] = {"@id": ORG_ID}; touched = True
                keep.append(n)
            g[:] = keep
            # priced Panama Offer on the 4 money pages
            if base_slug in PANAMA_OFFER_PAGES and not any(
                    isinstance(n, dict) and n.get("@type") == "Service" and n.get("offers") for n in g):
                g.append(PANAMA_OFFER); touched = True

        if "Article" in types:
            for n in g:
                if isinstance(n, dict) and n.get("@type") == "Article":
                    au = n.get("author")
                    if isinstance(au, dict):
                        if au.get("@id") != AUTHOR_ID:
                            au["@id"] = AUTHOR_ID; touched = True
                        if au.get("sameAs") != [LINKEDIN]:
                            au["sameAs"] = [LINKEDIN]; touched = True
                        if au.get("worksFor") != {"@id": ORG_ID}:
                            au["worksFor"] = {"@id": ORG_ID}; touched = True
                    if n.get("publisher") != {"@id": ORG_ID}:
                        n["publisher"] = {"@id": ORG_ID}; touched = True

        if touched:
            changed = True
            new_json = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
            new_h = new_h.replace(m.group(0), m.group(1) + new_json + m.group(3), 1)

    # visible breadcrumb nav for blogs
    if is_blog and '<a href="/jurisdictions/">Jurisdictions</a> &rsaquo;' in new_h:
        new_h = new_h.replace(
            '<nav class="breadcrumbs"><a href="/">Home</a> &rsaquo; <a href="/jurisdictions/">Jurisdictions</a> &rsaquo;',
            '<nav class="breadcrumbs"><a href="/">Home</a> &rsaquo; <a href="/blog/">Blog</a> &rsaquo;', 1)
        changed = True

    if changed and "--dry-run" not in sys.argv:
        open(path, "w", encoding="utf-8").write(new_h)
    return changed

def main():
    files = [f for f in glob.glob(os.path.join(ROOT, "**/index.html"), recursive=True) if "/node_modules/" not in f]
    n = sum(1 for f in files if repair(f))
    print(f"{'[dry] ' if '--dry-run' in sys.argv else ''}schema-repaired {n} / {len(files)} pages")

if __name__ == "__main__":
    main()
