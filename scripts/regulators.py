#!/usr/bin/env python3
"""
regulators.py — authoritative primary-source map (jurisdiction -> official regulator).
Used to inject a "Primary sources" citation block (E-E-A-T + LLM citability).
Only high-confidence, stable government/regulator homepages are listed.
"""

# base-slug -> (regulator display name, official homepage)
REGULATORS = {
 "lithuania": ("Bank of Lithuania", "https://www.lb.lt/en/"),
 "estonia": ("Finantsinspektsioon (Estonian FSA)", "https://www.fi.ee/en"),
 "cyprus": ("Cyprus Securities and Exchange Commission (CySEC)", "https://www.cysec.gov.cy/en-GB/home/"),
 "malta": ("Malta Financial Services Authority (MFSA)", "https://www.mfsa.mt/"),
 "czech-republic": ("Czech National Bank (CNB)", "https://www.cnb.cz/en/"),
 "poland": ("Polish Financial Supervision Authority (KNF)", "https://www.knf.gov.pl/en/"),
 "germany": ("BaFin", "https://www.bafin.de/EN/"),
 "france": ("Autorite des marches financiers (AMF)", "https://www.amf-france.org/en"),
 "spain": ("Comision Nacional del Mercado de Valores (CNMV)", "https://www.cnmv.es/portal/home.aspx?lang=en"),
 "italy": ("CONSOB", "https://www.consob.it/"),
 "netherlands": ("Authority for the Financial Markets (AFM)", "https://www.afm.nl/en"),
 "ireland": ("Central Bank of Ireland", "https://www.centralbank.ie/"),
 "portugal": ("Banco de Portugal", "https://www.bportugal.pt/en"),
 "bulgaria": ("Financial Supervision Commission (FSC Bulgaria)", "https://www.fsc.bg/en/"),
 "romania": ("Financial Supervisory Authority (ASF)", "https://asfromania.ro/en/"),
 "croatia": ("HANFA", "https://www.hanfa.hr/en/"),
 "greece": ("Hellenic Capital Market Commission", "https://www.hcmc.gr/"),
 "hungary": ("Magyar Nemzeti Bank (MNB)", "https://www.mnb.hu/en"),
 "slovakia": ("National Bank of Slovakia (NBS)", "https://nbs.sk/en/"),
 "latvia": ("Latvijas Banka", "https://www.bank.lv/en/"),
 "switzerland": ("Swiss Financial Market Supervisory Authority (FINMA)", "https://www.finma.ch/en/"),
 "dubai": ("Virtual Assets Regulatory Authority (VARA)", "https://www.vara.ae/"),
 "uae": ("Virtual Assets Regulatory Authority (VARA)", "https://www.vara.ae/"),
 "abu-dhabi": ("ADGM Financial Services Regulatory Authority", "https://www.adgm.com/"),
 "canada": ("FINTRAC", "https://fintrac-canafe.canada.ca/intro-eng"),
 "usa": ("Financial Crimes Enforcement Network (FinCEN)", "https://www.fincen.gov/"),
 "singapore": ("Monetary Authority of Singapore (MAS)", "https://www.mas.gov.sg/"),
 "hong-kong": ("Securities and Futures Commission (SFC)", "https://www.sfc.hk/en/"),
 "south-korea": ("Financial Services Commission (FSC Korea)", "https://www.fsc.go.kr/eng/"),
 "bvi": ("BVI Financial Services Commission", "https://www.bvifsc.vg/"),
 "cayman-islands": ("Cayman Islands Monetary Authority (CIMA)", "https://www.cima.ky/"),
 "bahamas": ("Securities Commission of The Bahamas", "https://www.scb.gov.bs/"),
 "bermuda": ("Bermuda Monetary Authority (BMA)", "https://www.bma.bm/"),
 "seychelles": ("Financial Services Authority Seychelles", "https://fsaseychelles.sc/"),
 "mauritius": ("Financial Services Commission Mauritius", "https://www.fscmauritius.org/"),
 "georgia": ("National Bank of Georgia", "https://nbg.gov.ge/en"),
 "el-salvador": ("Comision Nacional de Activos Digitales (CNAD)", "https://www.cnad.gob.sv/"),
 "south-africa": ("Financial Sector Conduct Authority (FSCA)", "https://www.fsca.co.za/"),
 "saudi-arabia": ("Saudi Central Bank (SAMA)", "https://www.sama.gov.sa/en-US/"),
 "qatar": ("Qatar Financial Centre Regulatory Authority", "https://www.qfcra.com/"),
 "isle-of-man": ("Isle of Man Financial Services Authority", "https://www.iomfsa.im/"),
 "labuan": ("Labuan Financial Services Authority", "https://www.labuanfsa.gov.my/"),
 "vanuatu": ("Vanuatu Financial Services Commission", "https://www.vfsc.vu/"),
 "panama": ("Unidad de Analisis Financiero (UAF Panama)", "https://www.uaf.gob.pa/"),
}

# shared EU/MiCA reference for topic pages that are EU-wide
MICA_SOURCE = ("European Securities and Markets Authority (ESMA) - MiCA",
               "https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica")

def regulator_for(slug: str):
    """Return (name, url) for a page slug, matching the longest jurisdiction base it contains."""
    s = slug.replace("-crypto-license", "")
    # direct/base match first (handles 'lithuania', 'lithuania-vs-x' -> first token group)
    for base in sorted(REGULATORS, key=len, reverse=True):
        if s == base or s.startswith(base + "-") or ("-" + base + "-") in ("-" + s + "-") or s.endswith("-" + base):
            return REGULATORS[base]
    # EU/MiCA topic pages
    if any(t in slug for t in ("mica", "casp")):
        return MICA_SOURCE
    return None

def sources_block(slug: str) -> str:
    """HTML 'Primary sources' citation block, or '' if no confident regulator."""
    r = regulator_for(slug)
    if not r:
        return ""
    name, url = r
    return ('<section class="primary-sources" style="margin:28px 0;padding:18px 20px;'
            'background:var(--surface);border:1px solid var(--line);border-radius:10px">'
            '<h2 style="font-size:1.15rem;margin:0 0 8px">Primary sources</h2>'
            '<p style="color:var(--ink-2);margin:0 0 8px;font-size:.92rem">'
            'This guide reflects 2026 rules. Verify current requirements with the official regulator:</p>'
            f'<ul style="margin:0;padding-left:20px"><li><a href="{url}" target="_blank" '
            f'rel="nofollow noopener">{name}</a></li>'
            f'<li><a href="{MICA_SOURCE[1]}" target="_blank" rel="nofollow noopener">{MICA_SOURCE[0]}</a></li>'
            '</ul></section>') if name != MICA_SOURCE[0] else (
            '<section class="primary-sources" style="margin:28px 0;padding:18px 20px;'
            'background:var(--surface);border:1px solid var(--line);border-radius:10px">'
            '<h2 style="font-size:1.15rem;margin:0 0 8px">Primary sources</h2>'
            f'<ul style="margin:0;padding-left:20px"><li><a href="{url}" target="_blank" '
            f'rel="nofollow noopener">{name}</a></li></ul></section>')
