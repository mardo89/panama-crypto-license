#!/usr/bin/env python3
"""YMYL correction: Panama has NO enacted crypto/VASP licence (2026) and the SSNF
does NOT license crypto (it is an AML supervisor for non-financial businesses like
casinos/real-estate, Law 23/2015). Draft Anteproyecto 314 (Jan 2026) is pending;
under it future supervision would sit with the SBP and UAF. The generated pages
invented an SSNF-run VASP licensing regime citing three fake laws (Law 61/2023,
Law 697). This rewrites every SSNF licensing claim to the accurate baseline:
a Panama company (Sociedad Anonima) + AML/CTF programme, no licence.

Deterministic exact-string replacement (longest-first so short fragments that are
substrings of longer ones are not corrupted). No em/en dashes (site QC style).
Run --dry-run to see residual SSNF/fake-law mentions before applying.

Verified 2026-07-20 (Chambers Blockchain 2026 - Panama; Uniwide).
"""
from __future__ import annotations
import glob, re, sys

# EXPLICIT Panama-fabrication list only. El Salvador pages (DASP / CNAD / Ley de
# Activos Digitales) are REAL and must NOT be touched. The AFIP page
# (how-to-get-a-crypto-license-in-panama-step-by-step) is redirected, not patched
# (23 fabricated-authority refs, wholesale-invented premise).
FILES = [
    "cost-crypto-license-panama/index.html",
    "panama-vs-switzerland-crypto-license/index.html",
    "easiest-crypto-license/index.html",
    "blog/moving-an-existing-crypto-business-to-panama-migration-checklist/index.html",
    "blog/canada-vs-panama-for-a-crypto-company-which-to-choose/index.html",
    "blog/hong-kong-vs-panama-for-a-crypto-company-which-to-choose/index.html",
    "blog/lithuania-vs-panama-for-a-crypto-company-which-to-choose/index.html",
    "blog/slovakia-vs-panama-for-a-crypto-company-which-should-you-choose/index.html",
    "blog/bahamas-vs-panama-for-a-crypto-company-which-should-you-choose/index.html",
    "blog/how-long-does-a-crypto-licence-take-timelines-by-jurisdiction/index.html",
]

# exact fragment -> accurate replacement (no double-quotes, no em/en dashes)
R = {
 "A crypto license in Panama is obtained through the registration of a Panama company with the Superintendencia de Sujetos No Financieros (SSNF) for virtual asset service provider (VASP) activities":
   "There is no crypto or VASP licence to obtain in Panama today; you operate through a registered Panama company with an AML/CTF compliance programme (a dedicated framework, Anteproyecto 314, is pending but not yet law)",
 "Applying for a VASP license from the SSNF":
   "Registering a Panama company and putting an AML/CTF programme in place",
 "Consulting24 offers a fixed fee of EUR 6,000 for a Panama company with SSNF registration":
   "Consulting24 offers a fixed fee of EUR 6,000 for a Panama company with a full AML/CTF compliance programme",
 "During this period, the SSNF may request additional documentation or clarifications":
   "During this period, the registered agent or your bank may request additional documentation or clarifications",
 "For example, a non-custodial wallet provider that never holds private keys may argue it is not a VASP, but the SSNF may still require registration if it facilitates transfers":
   "For example, a non-custodial wallet provider that never holds private keys is generally outside AML obligated-entity scope, whereas a service that holds funds or facilitates transfers should maintain an AML/CTF programme",
 "For example, in 2025, the SSNF fined several VASPs for inadequate CDD":
   "For example, Panama's AML authority (the UAF) expects obligated entities to maintain adequate customer due diligence",
 "However, the SSNF expects adequate capital for operations":
   "However, banks and payment partners expect adequate capital for operations",
 "However, the SSNF expects the company to have adequate capital to cover operational risks":
   "However, banks and payment partners expect the company to have adequate capital to cover operational risks",
 "However, the SSNF may require additional compliance measures depending on the services offered":
   "However, banking partners may require additional compliance measures depending on the services offered",
 "In practice, the SSNF may expect a reasonable amount based on business volume, but this is assessed case-by-case":
   "In practice, banking partners expect a reasonable amount based on business volume, assessed case-by-case",
 "Insufficient AML documentation: the SSNF expects detailed policies":
   "Insufficient AML documentation: banks and compliance reviews expect detailed policies",
 "No, if you provide virtual asset services in or from Panama, you need a VASP license from the SSNF":
   "No. Panama does not currently require a VASP licence, so there is no crypto licence to obtain; you operate through a Panama company with an AML/CTF programme",
 "Our team includes legal experts, compliance officers, and former regulators who understand the SSNF's expectations":
   "Our team includes legal experts, compliance officers, and former regulators who understand Panama's AML/CTF expectations",
 "Panama does not have a specific crypto law (unlike El Salvador), but the SSNF oversees compliance with anti-money laundering (AML) and counter-terrorism financing (CTF) obligations":
   "Panama does not have a specific crypto law (unlike El Salvador); crypto activity runs through a company that must meet Panama's anti-money laundering (AML) and counter-terrorism financing (CTF) obligations",
 "Panama offers a flat EUR 6,000 company setup, no capital gains tax on crypto, and a straightforward licensing process under the Superintendencia de Sujetos No Financieros (SSNF)":
   "Panama offers a flat EUR 6,000 company setup, no capital gains tax on foreign-source crypto income, and a straightforward company-formation-plus-AML process (no crypto licence is required today)",
 "Panama offers a straightforward registration process with the Superintendencia de Sujetos No Financieros (SSNF) under Law 23 of 2015, which regulates virtual asset service providers (VASPs)":
   "Panama offers a straightforward company-formation process; there is no VASP licensing regime today (a draft framework, Anteproyecto 314, is pending)",
 "Panama's SSNF also requires compliance but is less intrusive, focusing on annual renewal and ad-hoc checks":
   "Panama's approach is lighter, centred on the company's annual obligations and ongoing AML compliance",
 "Panama's SSNF is becoming more active in enforcement, so maintaining strong compliance is essential for trust with partners and banks":
   "Panama is tightening AML enforcement generally, so maintaining strong compliance is essential for trust with partners and banks",
 "Panama's SSNF registration is lighter but still demands KYC, transaction monitoring, and reporting":
   "Panama's compliance load is lighter but still demands KYC, transaction monitoring, and record-keeping",
 "Panama's regime is lighter but still demands a compliance manual, annual renewal, and cooperation with the SSNF":
   "Panama's regime is lighter but still demands a compliance manual, annual company renewal, and sound AML practices",
 "Panama’s SSNF conducts periodic reviews but is less intensive":
   "Panama’s compliance oversight is lighter and less intensive",
 "Prepare and submit application to SSNF with AML manual, business plan, and background checks":
   "Prepare the AML manual, business plan, and beneficial-owner background checks for the company file",
 "SSNF review (typically 4-6 weeks)":
   "AML compliance setup (typically 1-2 weeks)",
 "The entire process (company incorporation + SSNF registration) takes 2-4 weeks":
   "The entire process (company incorporation + AML compliance setup) takes 2-3 weeks",
 "The flat fee covers document preparation, liaison with the SSNF, and support until license issuance":
   "The flat fee covers document preparation, company incorporation, and AML/CTF compliance setup",
 "The license is issued by the Superintendencia de Sujetos No Financieros (SSNF) under Law 61 of 2023":
   "No crypto licence is issued in Panama today; a dedicated framework (Anteproyecto 314) is pending in the National Assembly",
 "The process is straightforward: incorporate a Panama corporation (Sociedad Anónima) and register it with the SSNF":
   "The process is straightforward: incorporate a Panama corporation (Sociedad Anónima) and put an AML/CTF compliance programme in place",
 "The regulator is the Superintendencia de Sujetos No Financieros (SSNF), which oversees VASP licensing under Law 697":
   "There is no crypto regulator or VASP licensing in Panama today; a draft framework (Anteproyecto 314) is pending",
 "The regulator is the Superintendencia de Sujetos No Financieros (SSNF)":
   "There is no dedicated crypto regulator in Panama today; a framework (Anteproyecto 314) is pending, under which supervision would sit with the SBP and UAF",
 "The timeline depends on the completeness of your documentation and the SSNF's workload":
   "The timeline depends mainly on the completeness of your documentation and company-registry processing",
 "The total cost Panama crypto license is EUR 6,000 flat, covering company incorporation, registered address, and registration with the SSNF":
   "The total cost is EUR 6,000 flat, covering company incorporation, registered address, and AML/CTF compliance setup",
 "The total cost is EUR 6,000 flat, covering company incorporation, registered address, and SSNF registration":
   "The total cost is EUR 6,000 flat, covering company incorporation, registered address, and AML/CTF compliance setup",
 "The Panama crypto license is not a traditional license but a registration as a Virtual Asset Service Provider (VASP) under the supervision of the SSNF":
   "There is no Panama crypto licence today; crypto activity runs through a Panama company with an AML/CTF programme (a dedicated VASP framework, Anteproyecto 314, is pending)",
 "The SSNF conducts on-site inspections and background checks on all beneficial owners":
   "Beneficial-owner background checks (KYC) are standard for company formation and banking",
 "The SSNF does not conduct on-site inspections but requires annual AML reports and may request information on request":
   "There is no crypto-specific regulator conducting inspections today; standard AML record-keeping and company annual filings apply",
 "The SSNF enforces AML/CFT compliance in line with FATF recommendations":
   "Panama enforces AML/CFT compliance in line with FATF recommendations",
 "The SSNF enforces strict AML compliance, and failure to comply can result in penalties":
   "Panama enforces AML compliance through its financial-intelligence unit (the UAF), and failure to comply can result in penalties",
 "The SSNF expects a clear description of services, target markets, and risk controls":
   "A sound AML programme includes a clear description of services, target markets, and risk controls",
 "The SSNF expects proper AML policies":
   "Banks and compliance reviews expect proper AML policies",
 "The SSNF is Panama's financial intelligence unit and AML supervisor":
   "The UAF (Unidad de Análisis Financiero) is Panama's financial intelligence unit and AML authority",
 "The SSNF is a dedicated non-financial supervisor with experience in AML/CFT oversight, having previously regulated other sectors like casinos and real estate agents":
   "Panama's AML supervisor for non-financial businesses (casinos, real-estate agents, precious-metals dealers) does not cover crypto companies, which fall outside its scope unless they also fit one of those categories",
 "The SSNF may also restrict certain high-risk activities like privacy coins or mixers":
   "Banks and payment partners typically restrict certain high-risk activities like privacy coins or mixers",
 "The SSNF oversees licensing, which is mandatory for custodial services, exchange, and transfer of virtual assets":
   "No licence is mandatory today for custody, exchange, or transfer of virtual assets in Panama (a framework is pending)",
 "The SSNF registration covers virtual asset exchange, transfer, custody, and wallet services":
   "A Panama company can be used for virtual asset exchange, transfer, custody, and wallet services, supported by an AML programme",
 "The SSNF requires strong AML/CTF procedures, including customer due diligence (CDD), transaction monitoring, and annual reporting":
   "Sound operations require strong AML/CTF procedures, including customer due diligence (CDD), transaction monitoring, and record-keeping",
 "The Superintendencia de Sujetos No Financieros (SSNF) oversees VASP registration":
   "Panama has no VASP registration regime today (a framework, Anteproyecto 314, is pending)",
 "The applicable registration is a VASP registration under the SSNF (Superintendencia de Sujetos No Financieros)":
   "There is no VASP registration in Panama today; the applicable setup is a Panama company with an AML/CTF programme",
 "There is no requirement to maintain a fixed amount after licensing, but the SSNF may review your capital adequacy during audits":
   "There is no fixed capital requirement, but banks may review your capital adequacy during onboarding",
 "There is no separate crypto law, but the SSNF has issued guidelines for virtual asset service providers":
   "There is no separate crypto law yet (a draft, Anteproyecto 314, is pending), so activity runs through a company under general AML rules",
 "This includes company incorporation (if needed) and SSNF review":
   "This includes company incorporation (if needed) and AML compliance setup",
 "This includes company incorporation, AML policy preparation, and SSNF review":
   "This includes company incorporation, AML policy preparation, and compliance setup",
 "VASP registration with SSNF (including AML manual, compliance officer appointment)":
   "AML/CTF programme setup (including AML manual and compliance officer appointment)",
 "You must maintain AML/CTF policies, conduct customer due diligence, monitor transactions, and file annual reports with the SSNF":
   "You must maintain AML/CTF policies, conduct customer due diligence, monitor transactions, and keep records in line with Panama's AML rules",
 "Prepare and submit application to SSNF with AML manual, business plan, and background checks":
   "Prepare the AML manual, business plan, and beneficial-owner background checks for the company file",
 "Submit application to SSNF with business plan, financials, background checks, and proof of office address":
   "Prepare the company file with business plan, financials, background checks, and proof of office address",
 "Submit application to SSNF with required fees":
   "Complete the company incorporation with required fees",
 "Submit registration to SSNF":
   "Complete the company registration",
 "Submission to SSNF":
   "Company filing",
 "submission to SSNF with all supporting documents":
   "preparation of the company file with all supporting documents",
 "SSNF review":
   "AML compliance setup",
 # bare entity / label catch-alls (applied last via length sort)
 "Superintendencia de Sujetos No Financieros (SSNF) - under Law 23 of 2015 (AML focus)":
   "Panama company plus AML compliance (Law 23 of 2015 governs AML for non-financial businesses; there is no crypto-specific licence today)",
 "Superintendencia de Sujetos No Financieros (SSNF)":
   "Panama's AML framework",
 # --- fake Panama laws / authorities (Law 697, Law 61 of 2023, Panama-DASP) ---
 "Panama, on the other hand, has enacted a dedicated crypto law (Law 697) that establishes a licensing regime for Virtual Asset Service Providers (VASPs)":
   "Panama, on the other hand, has no enacted crypto law yet (a draft, Anteproyecto 314, is pending); crypto activity runs through a Panama company with an AML/CTF programme",
 "Panama has a solid track record since Law 697 was enacted":
   "Panama has a solid track record as a corporate domicile for crypto companies",
 "Lithuania is fully MiCA-compliant; Panama has a dedicated crypto law (Law 61 of 2023) but lighter oversight":
   "Lithuania is fully MiCA-compliant; Panama has no dedicated crypto law yet (a draft, Anteproyecto 314, is pending) and lighter oversight",
 "In Panama, crypto activities are regulated under the <strong>Panama Crypto Law</strong> (Law 697 of 2024)":
   "In Panama, there is no dedicated crypto law yet (a draft, Anteproyecto 314, is pending) and crypto activity runs through a company with an AML/CTF programme",
 "In Panama, crypto activities are regulated under the Panama Crypto Law (Law 697 of 2024)":
   "In Panama, there is no dedicated crypto law yet (a draft, Anteproyecto 314, is pending) and crypto activity runs through a company with an AML/CTF programme",
 "Panama, by contrast, offers a dedicated crypto license under the Ley de Activos Digitales (Law 697), regulated by the Superintendencia de Bancos de Panamá (SBP)":
   "Panama, by contrast, has no dedicated crypto licence today; crypto activity runs through a Panama company with an AML/CTF programme (a draft framework, Anteproyecto 314, is pending)",
 "The license is a Digital Asset Service Provider (DASP) license under Law 697, regulated by the Superintendencia de Bancos de Panamá (SBP)":
   "There is no Panama crypto or DASP licence today; the setup is a Panama company with an AML/CTF programme",
 "Licensed DASPs can open accounts with local banks like Banco General or Banistmo, as well as international EMIs":
   "A Panama company with a strong AML programme can open accounts with local banks like Banco General or Banistmo, as well as international EMIs",
 "However, licensed DASPs can open accounts with local banks":
   "However, a Panama company with strong AML compliance can open accounts with local banks",
 "Panama (DASP):":
   "Panama (company + AML):",
 "DASP (Law 697)":
   "company + AML",
 "Superintendencia de Bancos de Panamá (SBP)":
   "Panama",
}


def apply(text):
    # longest first so a short key never eats into a longer one
    for k in sorted(R, key=len, reverse=True):
        text = text.replace(k, R[k])
    return text


def main():
    dry = "--dry-run" in sys.argv
    total = 0
    for f in FILES:
        s = open(f, encoding="utf-8").read()
        s2 = apply(s)
        n = s.count("SSNF") - s2.count("SSNF")
        total += n
        if not dry and s2 != s:
            open(f, "w", encoding="utf-8").write(s2)
        print(f"{'[dry] ' if dry else ''}{n:>2} SSNF claims fixed  {f}")
    # residuals on the FIXED pages only (never flag legit El Salvador pages)
    MARKERS = ("SSNF", "Law 61 of 2023", "Law 697", "AFIP",
               "Panama Financial Innovation", "Superintendencia de Sujetos No Financieros")
    print(f"\n{total} claims {'would be' if dry else ''} fixed across {len(FILES)} pages")
    print("--- residual fabrication markers on fixed pages ---")
    any_resid = False
    for f in FILES:
        h = open(f, encoding="utf-8").read() if not dry else apply(open(f, encoding="utf-8").read())
        for frag in re.findall(r'[^.>"]*(?:SSNF|Law 61 of 2023|Law 697|AFIP|Panama Financial Innovation)[^.<"]*', h):
            any_resid = True
            print(f"   RESIDUAL {f}: {frag.strip()[:110]}")
    if not any_resid:
        print("   none (fixed pages clean)")


if __name__ == "__main__":
    main()
