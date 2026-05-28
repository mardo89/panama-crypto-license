#!/usr/bin/env python3
"""
gen_blogger_pages.py — DeepSeek-powered pillar PAGE generator for Blogger.

Claude is the "brain" (topic list, fact briefs, schema, cleaning, QC gating);
DeepSeek writes the prose. Output is appended to config/extra_pages.json, which
consulting24_blog.py loads and merges into PAGES so `--pages` can publish them
(throttled, to respect the Blogger write quota).

Reads the DeepSeek key from $DEEPSEEK_API_KEY or scripts/.deepseek_key.
Idempotent: skips slugs already present in extra_pages.json or already posted.
"""
from __future__ import annotations
import json, os, pathlib, sys, urllib.request, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT  = ROOT / "config" / "extra_pages.json"
POSTED = ROOT / "config" / "blog_posted.json"

def key() -> str:
    k = os.environ.get("DEEPSEEK_API_KEY")
    if k: return k.strip()
    p = ROOT / "scripts" / ".deepseek_key"
    if p.exists(): return p.read_text().strip()
    sys.exit("No DeepSeek key (set DEEPSEEK_API_KEY or scripts/.deepseek_key)")

SITE = "https://www.consulting24.co"

SYSTEM = (
 "You are a senior crypto-licensing consultant writing an authoritative pillar guide for "
 "Consulting24 (X24Consulting OU, Estonia; founder Mardo Soo). Write in clear British-leaning "
 "professional English for crypto founders. Be accurate and specific. Treat the FACTS brief given "
 "in the prompt as authoritative and never contradict it. MiCA is in force across the EU in 2026; "
 "EU CASP capital tiers are EUR 50,000 / 125,000 / 150,000 by activity class. Do not invent precise "
 "figures that are not in the brief; if unsure, give a hedged range or say it depends. Panama has no "
 "dedicated crypto licence (incorporate a Sociedad Anonima). "
 "STYLE RULES (strict): no em dashes or en dashes, no exclamation marks, avoid the words "
 "'seamless, robust, leverage, navigate, landscape, realm, delve, unlock, elevate, tapestry, "
 "game-changer, cutting-edge'. Use plain sentences. "
 "Return ONLY a JSON object with this schema: "
 '{"tldr": "2-4 sentence summary, may contain simple HTML like <strong>", '
 '"sections": [ {"heading": "...", "paras": ["html paragraph", "..."]}, ... 2 to 3 sections ], '
 '"faqs": [ {"q": "...", "a": "..."}, ... exactly 4 ] }. '
 "Each section should have 2-3 substantial paragraphs. Paragraphs are plain text or simple inline HTML."
)

# (slug, title, keyword, landing-path-on-site, facts-brief)
TOPICS = [
 ("crypto-license-lithuania","Crypto License in Lithuania (MiCA CASP): Cost, Capital & Timeline 2026","crypto license Lithuania","/lithuania-crypto-license/",
  "Lithuania: Bank of Lithuania supervises; MiCA CASP authorisation; capital EUR 50k/125k/150k by activity class; full EU passporting; ~4-8 months; setup ~EUR 40,000 estimated. Consulting24 delivers this directly."),
 ("crypto-license-estonia","Crypto License in Estonia under MiCA: 2026 Setup Guide","crypto license Estonia","/estonia-crypto-license/",
  "Estonia: Finantsinspektsioon supervises; MiCA CASP replaced the old FIU/VASP registration; capital 50k/125k/150k; 0% tax on retained profit and 22% on distribution; ~5-9 months; e-Residency available. Consulting24 delivers this directly."),
 ("crypto-license-dubai","Crypto License in Dubai (VARA): How It Compares to Panama","crypto license Dubai","/dubai-crypto-license/",
  "Dubai: VARA category licences; premium cost; 0% personal income tax, 9% corporate with free-zone reliefs; DIFC/ADGM are separate regimes. Consulting24 does NOT deliver Dubai licensing; present this as a comparison only and steer delivery to Panama, Lithuania or Estonia."),
 ("crypto-license-canada","Canada MSB Crypto License (FINTRAC): 2026 Guide","crypto license Canada","/canada-crypto-license/",
  "Canada: FINTRAC MSB registration for dealing in virtual currency; provincial securities rules apply to tokens; among the faster routes, weeks to months; relatively low cost. Consulting24 advises and coordinates."),
 ("crypto-license-cyprus","Crypto License in Cyprus (MiCA CASP): 2026 Guide","crypto license Cyprus","/cyprus-crypto-license/",
  "Cyprus: CySEC supervises; MiCA CASP; capital 50k/125k/150k; English-speaking; favourable corporate tax; ~5-9 months. Consulting24 advises and coordinates."),
 ("crypto-license-malta","Crypto License in Malta (MiCA CASP): 2026 Guide","crypto license Malta","/malta-crypto-license/",
  "Malta: MFSA supervises; MiCA CASP built on the earlier VFA framework; capital 50k/125k/150k; English official language; ~5-9 months. Consulting24 advises and coordinates."),
 ("crypto-license-switzerland","Crypto License in Switzerland (FINMA, VQF): 2026 Guide","crypto license Switzerland","/switzerland-crypto-license/",
  "Switzerland: non-EU; FINMA regulates; routes include SRO/VQF AML membership, the DLT Act, and fintech or banking licences; Crypto Valley reputation; premium cost; ~6-12 months. Consulting24 advises and coordinates."),
 ("crypto-license-czech-republic","Crypto License in the Czech Republic (MiCA): 2026 Guide","crypto license Czech Republic","/czech-republic-crypto-license/",
  "Czech Republic: Czech National Bank supervises; MiCA CASP; capital 50k/125k/150k; cost-efficient EU option; ~4-8 months. Consulting24 advises and coordinates."),
 ("crypto-license-poland","Crypto License in Poland (MiCA CASP): 2026 Guide","crypto license Poland","/poland-crypto-license/",
  "Poland: KNF supervises; MiCA CASP; capital 50k/125k/150k; cost-efficient EU; ~4-8 months. Consulting24 advises and coordinates."),
 ("crypto-license-bvi","BVI Crypto License (VASP Act 2022): 2026 Guide","crypto license BVI","/bvi-crypto-license/",
  "BVI: BVI FSC supervises; VASP Act 2022; 0% corporate tax; suits token issuers and funds; ~3-6 months. Consulting24 advises and coordinates."),
 ("crypto-license-cayman-islands","Cayman Islands Crypto License (VASP Act): 2026 Guide","crypto license Cayman Islands","/cayman-islands-crypto-license/",
  "Cayman Islands: CIMA supervises; VASP Act; 0% direct tax; suits funds and token issuers; economic substance rules apply; ~3-6 months. Consulting24 advises and coordinates."),
 ("crypto-license-seychelles","Seychelles Crypto License (VASP Act 2024): 2026 Guide","crypto license Seychelles","/seychelles-crypto-license/",
  "Seychelles: FSA supervises; VASP Act 2024; low cost; 0% tax on foreign-source income; ~2-4 months. Consulting24 advises and coordinates."),
 ("crypto-license-georgia","Crypto License in Georgia (VASP): 2026 Guide","crypto license Georgia","/georgia-crypto-license/",
  "Georgia: National Bank of Georgia; VASP registration since 2023; low cost and fast, ~1-3 months. Consulting24 advises and coordinates."),
 ("crypto-license-mauritius","Crypto License in Mauritius (VAITOS Act): 2026 Guide","crypto license Mauritius","/mauritius-crypto-license/",
  "Mauritius: FSC supervises; VAITOS Act 2021 with several licence classes; ~3-6 months. Consulting24 advises and coordinates."),
 ("crypto-license-bahamas","Bahamas Crypto License (DARE Act 2024): 2026 Guide","crypto license Bahamas","/bahamas-crypto-license/",
  "Bahamas: Securities Commission; DARE Act 2024; 0% income tax; ~3-6 months. Consulting24 advises and coordinates."),
 ("crypto-license-el-salvador","El Salvador Crypto License (DASP/BSP): 2026 Guide","crypto license El Salvador","/el-salvador-crypto-license/",
  "El Salvador: CNAD supervises; DASP under the Digital Assets Issuance Law and BSP under the Bitcoin Law; Bitcoin is legal tender; tax incentives; ~3-6 months. Consulting24 advises and coordinates."),
 ("crypto-license-costa-rica","Crypto in Costa Rica vs Panama: 2026 Guide","crypto license Costa Rica","/costa-rica-crypto-license/",
  "Costa Rica: no dedicated crypto licence; operate via a general company plus an AML programme; commonly compared with Panama. Consulting24 advises and coordinates, and often recommends Panama."),
 ("crypto-license-singapore","Crypto License in Singapore (MAS PSA): 2026 Guide","crypto license Singapore","/singapore-crypto-license/",
  "Singapore: MAS supervises; Payment Services Act DPT licence; high regulatory bar, base capital and local presence required; ~9-18 months. Consulting24 advises and coordinates."),
 ("crypto-license-hong-kong","Crypto License in Hong Kong (SFC VATP): 2026 Guide","crypto license Hong Kong","/hong-kong-crypto-license/",
  "Hong Kong: SFC supervises; VATP licensing since 2023; high bar with local presence; ~9-12 months. Consulting24 advises and coordinates."),
 ("crypto-license-abu-dhabi","Crypto License in Abu Dhabi (ADGM FSRA): How It Compares to Panama","crypto license Abu Dhabi","/abu-dhabi-crypto-license/",
  "Abu Dhabi: ADGM FSRA crypto framework; premium cost. Consulting24 does NOT deliver this; present it as a comparison only and steer delivery to Panama, Lithuania or Estonia."),
 ("mica-license-guide","MiCA License Explained: CASP Authorisation in the EU (2026)","MiCA license","/mica-license/",
  "MiCA is the EU-wide regime in force in 2026; a CASP authorisation in one member state passports across the EU; capital tiers EUR 50k/125k/150k by activity class. Consulting24 delivers CASP in Lithuania and Estonia directly."),
 ("vasp-license-guide","VASP License Explained: Where and How to Register (2026)","VASP license","/vasp-license/",
  "VASP (Virtual Asset Service Provider) registrations exist in non-EU hubs such as BVI, Cayman, Seychelles and Georgia; in the EU the equivalent is now MiCA CASP. Consulting24 advises and coordinates, and delivers EU CASP directly."),
 ("casp-license-guide","CASP License Under MiCA: Requirements and Cost (2026)","CASP license","/casp-license/",
  "CASP is the MiCA crypto-asset service provider authorisation; capital EUR 50k/125k/150k by class; one authorisation passports across the EU; ~4-9 months depending on member state. Consulting24 delivers CASP in Lithuania and Estonia directly."),
 ("msb-license-guide","MSB License Explained: Canada FINTRAC and US FinCEN (2026)","MSB license","/msb-license/",
  "MSB (Money Services Business) registration covers virtual-currency dealing; Canada uses FINTRAC, the US uses FinCEN plus state money-transmitter rules; among the faster, lower-cost routes. Consulting24 advises and coordinates."),
 ("vara-license-guide","VARA License in Dubai: How It Compares to Panama (2026)","VARA license","/vara-license/",
  "VARA issues category licences for virtual assets in Dubai; premium cost and substance. Consulting24 does NOT deliver VARA; present it as a comparison only and steer delivery to Panama, Lithuania or Estonia."),
 ("stablecoin-license-guide","Stablecoin License: MiCA EMT/ART Rules and Alternatives (2026)","stablecoin license","/stablecoin-license/",
  "Under MiCA, stablecoins are regulated as e-money tokens (EMT) or asset-referenced tokens (ART) with issuer authorisation and reserve rules; non-EU issuance uses other frameworks. Consulting24 advises and coordinates, and delivers EU routes directly."),
 ("cheapest-crypto-license","Cheapest Crypto License Options in 2026 (Honest Comparison)","cheapest crypto license","/cheapest-crypto-license/",
  "Lower-cost routes include Panama incorporation, Canada MSB, Georgia VASP and Seychelles VASP; cheap does not mean suitable for EU retail, which needs MiCA CASP. Panama is roughly USD 15,000-45,000 all-in year one. Consulting24 delivers Panama and EU CASP."),
 ("fastest-crypto-license","Fastest Crypto License Routes in 2026","fastest crypto license","/fastest-crypto-license/",
  "Faster routes include Panama incorporation (2-3 weeks), Georgia VASP (~1-3 months) and Canada MSB (weeks to months); EU MiCA CASP takes longer at ~4-9 months. Consulting24 delivers Panama and EU CASP."),
 ("easiest-crypto-license","Easiest Crypto License to Get in 2026","easiest crypto license","/easiest-crypto-license/",
  "Ease depends on your customers; offshore routes like Panama, Seychelles and Georgia have lower bars, while EU CASP and Singapore are more demanding. Consulting24 delivers Panama and EU CASP."),
 ("ready-made-crypto-license","Ready-Made Crypto License Companies: What to Know in 2026","ready-made crypto license","/ready-made-crypto-license/",
  "Shelf or ready-made crypto companies can shorten setup but carry due-diligence and history risk; most regulators still require fresh fit-and-proper checks. Consulting24 advises and coordinates and usually recommends a clean new entity."),
 ("crypto-license-requirements","Crypto License Requirements: Documents and Compliance (2026)","crypto license requirements","/requirements/",
  "Typical requirements: corporate entity, fit-and-proper directors and UBOs, AML/KYC programme, source-of-funds evidence, and for EU CASP the capital tiers EUR 50k/125k/150k. Consulting24 prepares and coordinates the full file."),
 ("crypto-company-setup","Crypto Company Setup: Structure, Banking and Tax (2026)","crypto company setup","/company-setup/",
  "A clean operating entity plus a separate vehicle for any token or treasury is common; banking and payment rails are the main gating factor everywhere. Panama incorporation takes 2-3 weeks. Consulting24 delivers Panama and EU CASP."),
 ("best-country-for-crypto-license","Best Country for a Crypto License in 2026 (by Use Case)","best country for crypto license","/best-country-for-crypto-license/",
  "There is no single best country; EU retail needs MiCA CASP (Lithuania, Estonia), North American fiat fits Canada MSB, offshore and HNW often choose Panama. Consulting24 delivers Panama and EU CASP and advises on the rest."),
 ("estonia-vs-lithuania-crypto-license","Estonia vs Lithuania for a Crypto License (MiCA) in 2026","Estonia vs Lithuania crypto license","/estonia-vs-lithuania-crypto-license/",
  "Both are EU MiCA CASP jurisdictions with capital 50k/125k/150k; Estonia offers 0% tax on retained profit and e-Residency, Lithuania has a deep fintech ecosystem and Bank of Lithuania supervision. Consulting24 delivers both directly."),
 ("panama-vs-dubai-crypto-license","Panama vs Dubai for a Crypto License in 2026","Panama vs Dubai crypto license","/panama-vs-dubai-crypto-license/",
  "Panama: no dedicated licence, 2-3 week incorporation, ~USD 15,000-45,000 year one, 0% on foreign-source income. Dubai VARA: premium category licences with substance. Consulting24 delivers Panama; Dubai is presented as a comparison only."),
]

BANNED = {
 "seamless":"smooth","seamlessly":"smoothly","robust":"strong","leverage":"use",
 "leveraging":"using","navigate":"handle","navigating":"handling","landscape":"market",
 "realm":"area","delve":"look","unlock":"open","elevate":"improve","tapestry":"mix",
 "game-changer":"major shift","cutting-edge":"modern",
}

def clean(s: str) -> str:
    if not s: return s
    s = s.replace("—", ", ").replace("–", "-")  # em/en dash -> comma / hyphen
    s = s.replace(" ,", ",").replace("!", ".")
    for b, r in BANNED.items():
        s = re.sub(rf"\b{re.escape(b)}\b", r, s, flags=re.I)
    s = re.sub(r"\.{2,}", ".", s)
    return s.strip()

def call_deepseek(user: str) -> dict:
    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role":"system","content":SYSTEM},{"role":"user","content":user}],
        "response_format": {"type":"json_object"},
        "max_tokens": 6000, "temperature": 0.6, "stream": False,
    }).encode()
    req = urllib.request.Request("https://api.deepseek.com/chat/completions", data=body,
        headers={"Content-Type":"application/json","Authorization":"Bearer "+key()})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.load(r)
    return json.loads(data["choices"][0]["message"]["content"])

def build_page(slug, title, keyword, landing, brief) -> dict:
    user = (
        f"Write a pillar guide titled '{title}'. Primary keyword: '{keyword}'. "
        f"FACTS (authoritative): {brief} "
        f"The on-site landing page for conversions is {SITE}{landing} (you may reference it as the relevant page). "
        "Write 2 to 3 sections and exactly 4 FAQs as per the schema."
    )
    d = call_deepseek(user)
    sections = []
    for s in d.get("sections", [])[:3]:
        h = clean(s.get("heading",""))
        paras = [clean(p) for p in s.get("paras",[]) if p and p.strip()]
        if h and paras:
            sections.append([h, paras])
    faqs = []
    for f in d.get("faqs", [])[:4]:
        q = clean(f.get("q","")); a = clean(f.get("a",""))
        if q and a: faqs.append([q, a])
    while len(faqs) < 4:  # guard; pad rarely needed
        faqs.append([f"Does Consulting24 help with {keyword}?",
                     "Yes. Consulting24 advises on jurisdiction choice and coordinates or delivers the setup. Contact mardo@consulting24.co."])
    return {
        "slug": slug, "title": clean(title), "keyword": keyword, "landing": landing,
        "tldr": clean(d.get("tldr","")), "table": True,
        "sections": sections[:3] if sections else [[ "Overview", [clean(brief)] ]],
        "faqs": faqs[:4],
    }

def main():
    existing = json.loads(OUT.read_text()) if OUT.exists() else []
    have = {p["slug"] for p in existing}
    posted = set()
    if POSTED.exists():
        posted = set(json.loads(POSTED.read_text()).get("pages", {}).keys())
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(TOPICS)
    made = 0
    for slug, title, keyword, landing, brief in TOPICS:
        if made >= limit: break
        if slug in have or slug in posted:
            print(f"skip {slug} (already generated/posted)"); continue
        try:
            page = build_page(slug, title, keyword, landing, brief)
            existing.append(page); have.add(slug); made += 1
            OUT.write_text(json.dumps(existing, indent=1, ensure_ascii=False))
            print(f"generated [{made}] {slug} ({len(page['sections'])} sections, {len(page['faqs'])} faqs)")
        except Exception as e:
            print(f"ERROR {slug}: {e}")
    print(f"done. {made} new pages; {len(existing)} total in {OUT}")

if __name__ == "__main__":
    main()
