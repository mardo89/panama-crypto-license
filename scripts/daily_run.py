#!/usr/bin/env python3
"""
daily_run.py — fully autonomous daily content pipeline for consulting24.co.
Runs WITHOUT an interactive agent (designed for a macOS LaunchAgent / cron).
Publishes 40 keyword landing pages + 40 blog posts/day via DeepSeek + QC gate,
rebuilds indexes, links, sitemap/IndexNow, commits and pushes.

Brief composition is automated: known jurisdictions use a curated FACTS map
(accurate 2026 facts); long-tail items get a guard-railed generic brief and
rely on the generator's accuracy + QC gates. Deck-fed pages (e.g. Lithuania)
keep their hand-verified figures unless overwritten here.
"""
import os, re, sys, subprocess, importlib.util, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N_LANDING = int(os.environ.get("N_LANDING", "40"))
N_BLOG = int(os.environ.get("N_BLOG", "40"))

spec = importlib.util.spec_from_file_location("gen", os.path.join(ROOT, "scripts", "generate.py"))
gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)

# Curated accurate facts for major jurisdictions (base slug -> brief facts).
FACTS = {
 "lithuania": "Lithuania | Bank of Lithuania; MiCAR CASP; capital EUR 50k/125k/150k by activity; EU passporting; ~4-8 months; setup ~EUR 40,000 (estimated); Consulting24 delivers directly.",
 "estonia": "Estonia | Finantsinspektsioon; MiCA CASP (replaced FIU/VASP); capital 50k/125k/150k; 0% on retained profit, 22% on distribution; ~5-9 months; e-Residency; Consulting24 delivers directly.",
 "czech-republic": "Czech Republic | Czech National Bank; MiCA CASP; capital 50k/125k/150k; cost-efficient EU; ~4-8 months; Consulting24 advises and coordinates.",
 "poland": "Poland | KNF; MiCA CASP; capital 50k/125k/150k; cost-efficient EU; ~4-8 months; Consulting24 advises and coordinates.",
 "malta": "Malta | MFSA; MiCA CASP (built on VFA); capital 50k/125k/150k; English official; ~5-9 months; Consulting24 advises and coordinates.",
 "cyprus": "Cyprus | CySEC; MiCA CASP; capital 50k/125k/150k; English; favourable tax; ~5-9 months; Consulting24 advises and coordinates.",
 "switzerland": "Switzerland | non-EU; FINMA; SRO/VQF AML membership, DLT Act, fintech/banking licences; Crypto Valley; premium; ~6-12 months; Consulting24 advises and coordinates.",
 "cayman-islands": "Cayman Islands | CIMA; VASP Act; 0% direct tax; funds and token issuers; economic substance; ~3-6 months; Consulting24 advises and coordinates.",
 "bvi": "BVI | BVI FSC; VASP Act 2022; 0% corporate tax; token issuers/funds; ~3-6 months; Consulting24 advises and coordinates.",
 "seychelles": "Seychelles | FSA; VASP Act 2024; low cost; 0% foreign-source tax; ~2-4 months; Consulting24 advises and coordinates.",
 "canada": "Canada | FINTRAC MSB registration for virtual currency dealing; provincial securities for tokens; weeks-months; Consulting24 advises and coordinates.",
 "singapore": "Singapore | MAS; Payment Services Act DPT licence; high bar, base capital, local presence; ~9-18 months; Consulting24 advises and coordinates.",
 "hong-kong": "Hong Kong | SFC; VATP licensing since 2023; high bar, local presence; ~9-12 months; Consulting24 advises and coordinates.",
 "georgia": "Georgia | National Bank of Georgia; VASP registration (from 2023); low cost, fast ~1-3 months; Consulting24 advises and coordinates.",
 "mauritius": "Mauritius | FSC; VAITOS Act 2021 licence classes; ~3-6 months; Consulting24 advises and coordinates.",
 "gibraltar": "Gibraltar | GFSC; DLT Provider licence since 2018; reputable; ~3-6 months; Consulting24 advises and coordinates.",
 "bahamas": "Bahamas | Securities Commission; DARE Act 2024; 0% income tax; ~3-6 months; Consulting24 advises and coordinates.",
 "costa-rica": "Costa Rica | no dedicated crypto licence; general company + AML; strong Panama comparison; Consulting24 advises and coordinates.",
 "el-salvador": "El Salvador | CNAD; DASP (Digital Assets Issuance Law) + BSP (Bitcoin Law); Bitcoin legal tender; tax incentives; ~3-6 months; Consulting24 advises and coordinates.",
 "dubai": "Dubai | VARA category licences; premium; 0% personal, 9% corporate (free-zone reliefs); DIFC/ADGM separate; DELIVERY=comparison-only.",
 "abu-dhabi": "Abu Dhabi | ADGM FSRA crypto framework; premium; DELIVERY=comparison-only.",
}
COMPARISON_ONLY = {"dubai", "abu-dhabi", "uae"}

def sh(cmd):
    return subprocess.run(cmd, cwd=ROOT, shell=True, text=True, capture_output=True)

def base_of(slug):
    return slug.replace("-crypto-license", "")

def landing_brief(slug):
    b = base_of(slug)
    if b in FACTS: return FACTS[b]
    name = b.replace("-", " ").title()
    extra = " DELIVERY=comparison-only." if b in COMPARISON_ONLY else " Consulting24 advises and coordinates."
    return (f"{name} | Use accurate, current 2026 facts for this crypto-licensing topic: the relevant "
            f"regulator, licence/registration type, capital, tax, timeline and allowed activities. "
            f"If unsure of a specific figure, give a hedged range and defer exact pricing to a consultation."
            f"{extra}")

def keyword_from(slug):
    return base_of(slug).replace("-", " ").strip() + " crypto license"

def next_unchecked(md_path, n):
    out = []
    for line in open(md_path, encoding="utf-8"):
        m = re.match(r"- \[ \] (.+)", line.strip())
        if m: out.append(m.group(1).strip())
        if len(out) >= n: break
    return out

def mark_done(md_path, needle):
    s = open(md_path, encoding="utf-8").read()
    s = s.replace(f"- [ ] {needle}", f"- [x] {needle}", 1)
    open(md_path, "w", encoding="utf-8").write(s)

def slugify(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:70]

def run():
    sh("git pull --no-edit origin main")
    published = []
    CHUNK = int(os.environ.get("CHUNK", "5"))   # commit+push every CHUNK pages so a kill never loses progress

    def checkpoint(force=False):
        if not published: return
        if not force and len(published) % CHUNK != 0: return
        sh("python3 scripts/rebuild_indexes.py")
        sh("python3 scripts/publish.py")
        sh("git add -A")
        sh(f'git commit -q -m "Auto-publish checkpoint: {len(published)} pages ({datetime.date.today()})\n\nCo-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"')
        out = sh("git push origin main")
        print(f"checkpoint pushed at {len(published)} pages {out.stderr[-120:]}")

    # --- landing pages ---
    for entry in next_unchecked(os.path.join(ROOT, "pages.md"), N_LANDING):
        m = re.search(r"([a-z0-9-]+)\s*(?:→|->)\s*/([a-z0-9-]+)/", entry)
        slug = (m.group(2) if m else entry.split()[0]).strip("/")
        try:
            rep = gen.build("landing", slug, keyword_from(slug), landing_brief(slug))
            if rep.get("pass"): published.append("/"+slug+"/")
        except Exception as e:
            print("landing err", slug, e)
        mark_done(os.path.join(ROOT, "pages.md"), entry)
        checkpoint()
    # --- blog posts ---
    for title in next_unchecked(os.path.join(ROOT, "blog", "topics.md"), N_BLOG):
        slug = slugify(title)
        kw = " ".join(title.split()[:4])
        brief = f"{title} | Educational, accurate 2026 guidance for crypto founders. Internal-link to relevant jurisdiction pages and Panama. Consulting24 context."
        try:
            rep = gen.build("blog", slug, kw, brief)
            if rep.get("pass"): published.append("/blog/"+slug+"/")
        except Exception as e:
            print("blog err", slug, e)
        mark_done(os.path.join(ROOT, "blog", "topics.md"), title)
        checkpoint()
    print(sh("python3 scripts/linkcheck.py").stdout[-400:])
    checkpoint(force=True)   # final flush of the remainder
    print(f"DONE: published {len(published)} pages")

if __name__ == "__main__":
    run()
