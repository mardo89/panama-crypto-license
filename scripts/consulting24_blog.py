#!/usr/bin/env python3
"""Consulting24 / Crypto License Panama — daily Blogger content pipeline.

Posts AI-written, long-form SEO articles about crypto licensing to a Blogger
blog owned by mardo@consulting24.co, each linking back to consulting24.co
landing pages.

This is a SEPARATE project from boat-rental-marbella. It reuses the same
Google OAuth *desktop client* (the client_secret JSON is account-agnostic),
but authorises as mardo@consulting24.co and stores its own token at
  ~/.consulting24_blogger_token.json
so the two projects never share Blogger credentials.

State:  config/blog_posted.json   (keyed by article slug — each posted once)
Topics: ARTICLES list below (authored long-form content, text-only)

Setup:
  GOOGLE_CREDENTIALS=/path/to/client_secret_desktop.json   (in .env)
  BLOGGER_BLOG_ID=<consulting24 blog id>                    (in .env)
  python3 scripts/consulting24_blog.py --login        # one-time OAuth as mardo@
  python3 scripts/consulting24_blog.py --list         # show queue + posted state
  python3 scripts/consulting24_blog.py --dry-run      # render next post, no publish
  python3 scripts/consulting24_blog.py                # publish today's batch
  python3 scripts/consulting24_blog.py --once SLUG    # publish one specific slug
"""
from __future__ import annotations

import argparse, json, os, pathlib, sys, datetime, traceback

ROOT        = pathlib.Path(__file__).resolve().parents[1]
STATE_PATH  = ROOT / "config" / "blog_posted.json"
LOG_DIR     = ROOT / "logs"
LOG_PATH    = LOG_DIR / "consulting24_blog.log"
TOKEN_PATH  = pathlib.Path.home() / ".consulting24_blogger_token.json"

SITE        = "https://www.consulting24.co"
EMAIL       = "mardo@consulting24.co"
PHONE       = "+372 58155779"
DAILY_LIMIT = 5          # articles published per run/day

# Blogger only — no Drive access needed for this project.
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/blogger"]

LOG_DIR.mkdir(exist_ok=True)

# ── logging ────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a") as fh:
        fh.write(line + "\n")

# ── env ────────────────────────────────────────────────────────────────────

def load_env():
    for p in [ROOT / ".env", pathlib.Path.home() / ".env"]:
        if p.exists():
            for line in p.read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    k = k.strip()
                    if k and k not in os.environ:
                        os.environ[k] = v.strip().strip('"').strip("'")

load_env()

def require_env(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if not v:
        sys.exit(f"ERROR: {name} is not set. See file header for setup instructions.")
    return v

# ── Google OAuth (Blogger) ──────────────────────────────────────────────────

def get_credentials():
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    creds_path = pathlib.Path(require_env("GOOGLE_CREDENTIALS"))
    if not creds_path.exists():
        sys.exit(f"ERROR: GOOGLE_CREDENTIALS not found: {creds_path}")

    raw = json.loads(creds_path.read_text())
    if raw.get("type") == "service_account":
        sys.exit("ERROR: Blogger needs OAuth user credentials, not a service account.")

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), GOOGLE_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), GOOGLE_SCOPES)
            print("\n>>> A browser window will open. Sign in as", EMAIL, "<<<\n")
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return creds

def build_blogger(creds):
    from googleapiclient.discovery import build
    return build("blogger", "v3", credentials=creds, cache_discovery=False)

# ── state ───────────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"posts": {}}

def save_state(state: dict):
    STATE_PATH.write_text(json.dumps(state, indent=2))

def posted(state: dict, slug: str) -> bool:
    return slug in state.get("posts", {})

def mark_posted(state: dict, slug: str, meta: dict):
    state.setdefault("posts", {})[slug] = {
        **meta, "posted_at": datetime.datetime.now().isoformat(),
    }

# ── shared HTML blocks ───────────────────────────────────────────────────────

def _cta(keyword: str, landing_path: str) -> str:
    url = f"{SITE}{landing_path}"
    wa = PHONE.replace("+", "").replace(" ", "")
    return f"""
<div style="background:#0b1f3a;color:#fff;padding:22px 26px;margin:34px 0;border-radius:8px;">
  <strong style="font-size:18px;">Ready to set up your {keyword}?</strong>
  <p style="margin:10px 0 16px;color:#cfe0f5;">Consulting24 has completed 200+ crypto company
  setups across 15+ jurisdictions. Talk to our team for a fixed-fee proposal and realistic timeline.</p>
  <a href="{url}" style="background:#1e88e5;color:#fff;padding:11px 22px;border-radius:5px;text-decoration:none;font-weight:bold;display:inline-block;margin-right:10px;">Learn more</a>
  <a href="https://wa.me/{wa}" style="background:#25D366;color:#fff;padding:11px 22px;border-radius:5px;text-decoration:none;font-weight:bold;display:inline-block;">WhatsApp us</a>
  <p style="margin:14px 0 0;color:#9fb6d4;font-size:13px;">Email <a href="mailto:{EMAIL}" style="color:#fff;">{EMAIL}</a> &middot; Phone {PHONE}</p>
</div>"""

def _faq(faqs: list[tuple[str, str]]) -> str:
    items = "".join(
        f'<h3 style="margin-top:22px;">{q}</h3><p>{a}</p>' for q, a in faqs
    )
    return f"<h2>Frequently Asked Questions</h2>{items}"

def _related(related: list[tuple[str, str]]) -> str:
    items = "".join(f'<li><a href="{SITE}{path}">{label}</a></li>' for label, path in related)
    return f"<h2>Related reading</h2><ul>{items}</ul>"

def _disclaimer() -> str:
    return ("<p style='color:#777;font-size:13px;margin-top:28px;border-top:1px solid #eee;"
            "padding-top:14px;'><em>This article reflects 2026 market conditions and is general "
            "guidance, not legal or tax advice. Regulations change &mdash; confirm specifics with "
            "qualified counsel before acting. Consulting24 (X24Consulting O&Uuml;, Estonian reg. "
            "16971898) introduces vetted local lawyers and tax advisors during every engagement.</em></p>")

def render_article(topic: dict) -> str:
    """Build the full post HTML from a topic spec."""
    parts = [f"<p><strong>{topic['lede']}</strong></p>"]
    for heading, paras in topic["sections"]:
        parts.append(f"<h2>{heading}</h2>")
        for p in paras:
            parts.append(f"<p>{p}</p>")
    parts.append(_cta(topic["keyword"], topic["landing"]))
    parts.append(_faq(topic["faqs"]))
    parts.append(_related(topic["related"]))
    parts.append(_disclaimer())
    return "\n".join(parts)

# ── articles ────────────────────────────────────────────────────────────────
# Each topic: slug, title, keyword, landing (internal path), labels (Blogger
# tags), lede, sections [(h2, [paragraphs])], faqs [(q, a)], related [(label,path)].

PANAMA_ARTICLES: list[dict] = [
    {
        "slug": "crypto-license-panama-2026-guide",
        "title": "Crypto License in Panama 2026: The Complete Setup Guide",
        "keyword": "crypto license in Panama",
        "landing": "/",
        "labels": ["Panama", "Crypto License", "Guide"],
        "lede": "Panama has quietly become one of the most practical bases for crypto businesses "
                "that serve Latin America, Asia and high-net-worth clients rather than EU retail. "
                "Here is exactly how a crypto company is set up in Panama in 2026, what it costs, "
                "and when it is the right choice.",
        "sections": [
            ("Does Panama Have a Crypto License?",
             ["Panama does <strong>not</strong> have a single dedicated crypto or VASP license as of 2026. "
              "Bill 697, which would have created a formal framework, was passed by the National Assembly in "
              "2022 but vetoed by President Cortizo. Reform discussions continue, but no standalone regime "
              "has been enacted.",
              "Instead, crypto activities operate under Panama's existing financial-services frameworks. "
              "Money-services activities fall under the Superintendency of Banks of Panama (SBP), and AML/CFT "
              "supervision sits with UAF Panama (Unidad de An&aacute;lisis Financiero), the local equivalent of "
              "FinCEN in the US or FINTRAC in Canada. In practice, most crypto operators incorporate a Panama "
              "Sociedad An&oacute;nima and run a documented AML/KYC program rather than holding a named license."]),
            ("The Two Core Structures",
             ["<strong>Panama Sociedad An&oacute;nima (S.A.)</strong> is the workhorse corporation for exchanges, "
              "brokers and payment processors. It incorporates in 2&ndash;3 weeks, requires three directors "
              "(nominees are permitted), and has no minimum paid-up capital.",
              "<strong>Panama Private Interest Foundation</strong> is an asset-protection structure used for "
              "token treasuries, family-office crypto holdings and DAO foundations. It requires a minimum "
              "endowment of roughly $10,000 and is frequently paired with an operating S.A."]),
            ("What It Costs and How Long It Takes",
             ["Budget $15,000&ndash;$45,000 all-in for the first year, depending on whether you need a full "
              "AML/KYC compliance program, banking introductions and ongoing nominee services. Annual "
              "maintenance runs $5,000&ndash;$15,000.",
              "End-to-end timelines are typically 6&ndash;12 weeks &mdash; materially faster than the 4&ndash;8 months "
              "a Lithuania MiCA VASP authorisation now takes. See our full "
              f"<a href='{SITE}/cost/'>cost breakdown</a> and "
              f"<a href='{SITE}/application-process/'>application process</a> for the line-item detail."]),
            ("Tax and Banking Reality",
             ["Panama runs a territorial tax system: foreign-source income is taxed at 0%. The country also uses "
              "the US dollar as legal tender alongside the balboa at a 1:1 peg, so there is no FX risk on "
              "USD-denominated crypto operations.",
              "Banking is the real bottleneck. Panamanian banks have tightened KYC for crypto-adjacent businesses "
              "since 2023, so expect 2&ndash;5 weeks for onboarding and a properly documented source-of-funds and "
              "compliance file. Panama was removed from the FATF grey list in October 2023 and is FATF-compliant "
              "in 2026, which has helped restore correspondent-banking confidence."]),
        ],
        "faqs": [
            ("Is crypto legal in Panama?",
             "Yes. Holding, trading and operating crypto businesses is legal. There is simply no dedicated "
             "licensing regime; activities run under existing financial-services and AML law."),
            ("How fast can I incorporate?",
             "A Panama S.A. incorporates in 2&ndash;3 weeks. Full operational readiness including banking and a "
             "compliance program is usually 6&ndash;12 weeks."),
            ("Do I need to live in Panama?",
             "No. Directors and shareholders can be non-resident, and nominee directors are permitted. You do "
             "need a registered agent in Panama, which we arrange."),
        ],
        "related": [
            ("Panama crypto company setup", "/company-setup/"),
            ("Requirements checklist", "/requirements/"),
            ("Panama vs Lithuania", "/vs-lithuania/"),
        ],
    },
    {
        "slug": "panama-vs-lithuania-crypto-license",
        "title": "Panama vs Lithuania for a Crypto License: Which Should You Choose in 2026?",
        "keyword": "crypto license comparison",
        "landing": "/vs-lithuania/",
        "labels": ["Panama", "Lithuania", "Comparison", "MiCA"],
        "lede": "The single most common question we get: should I license in Panama or Lithuania? "
                "The honest answer depends entirely on who your customers are. Here is the decision "
                "framework we use with clients.",
        "sections": [
            ("The Headline Trade-off",
             ["Lithuania gives you an EU MiCA passport &mdash; the ability to serve EU retail customers under a "
              "recognised European regulator. That credibility costs money and time: roughly $50,000&ndash;$120,000 "
              "to set up and 4&ndash;8 months to authorise.",
              "Panama gives you speed, low cost and territorial-tax efficiency, but no EU passport. Setup is "
              "$15,000&ndash;$45,000 and 6&ndash;12 weeks. It is built for offshore-first operations that do not need "
              "to touch EU retail."]),
            ("Choose Lithuania If...",
             ["You are launching a public-facing exchange targeting EU retail customers and need the MiCA "
              "passport to operate legally across the bloc.",
              "You want the reputational lift of an EU regulator badge for institutional partners, banking and "
              "fundraising. For many CEX projects this badge alone justifies the cost."]),
            ("Choose Panama If...",
             ["Your customers are in Latin America, Asia, or you serve high-net-worth individuals rather than EU "
              "retail. You do not need a MiCA passport and would rather not pay for one.",
              "You prioritise fast incorporation and a lower regulatory burden, and you value Panama's 0% tax on "
              "foreign-source income. Many token treasuries and brokers fit this profile precisely.",
              f"See the side-by-side detail on our <a href='{SITE}/vs-lithuania/'>Panama vs Lithuania</a> page."]),
            ("What About Other Jurisdictions?",
             ["<strong>Canada MSB (FINTRAC):</strong> $8,000&ndash;$25,000, 3&ndash;6 weeks, strong North American fiat "
              "rails &mdash; best for crypto-to-fiat exchanges. <strong>BVI VASP:</strong> a similar offshore profile "
              "to Panama with slightly higher cost and more legal certainty post-VASP Act 2022. "
              "<strong>Estonia VASP:</strong> largely deprecated after the 2024 crackdown; most operators have "
              "migrated to Lithuania."]),
        ],
        "faqs": [
            ("Can I start in Panama and move to Lithuania later?",
             "Yes, and many do. Launching offshore in Panama to validate the business, then adding an EU entity "
             "for MiCA passporting once revenue justifies it, is a common staged approach."),
            ("Does Panama recognise MiCA?",
             "No. Panama is outside the EU and not bound by MiCA. If your business model depends on serving EU "
             "retail, Panama alone is not sufficient."),
            ("Which is cheaper to maintain?",
             "Panama. Annual maintenance is $5,000&ndash;$15,000 versus materially higher ongoing compliance and "
             "reporting costs under an EU MiCA framework."),
        ],
        "related": [
            ("Panama crypto license overview", "/"),
            ("Cost breakdown", "/cost/"),
            ("Exchange license options", "/exchange-license/"),
        ],
    },
    {
        "slug": "panama-crypto-company-cost-breakdown-2026",
        "title": "How Much Does a Panama Crypto Company Cost in 2026? Full Breakdown",
        "keyword": "Panama crypto company cost",
        "landing": "/cost/",
        "labels": ["Panama", "Cost", "Crypto License"],
        "lede": "Crypto setup quotes vary wildly because providers bundle different things. Here is an "
                "honest, line-item view of what a Panama crypto company actually costs in 2026 &mdash; "
                "first year and ongoing.",
        "sections": [
            ("First-Year Total: $15,000&ndash;$45,000",
             ["The range is wide because it depends on how much you need. A lean Sociedad An&oacute;nima with a "
              "registered agent and basic structure sits near the bottom. A full build &mdash; S.A. plus a "
              "documented AML/KYC program, banking introductions, nominee directors and a foundation for the "
              "treasury &mdash; sits near the top.",
              f"Our <a href='{SITE}/cost/'>cost page</a> breaks these into fixed packages so there are no surprises."]),
            ("Where the Money Goes",
             ["<strong>Incorporation of the Sociedad An&oacute;nima:</strong> government fees, registered agent, "
              "and corporate documents. <strong>AML/KYC compliance program:</strong> from roughly $8,000 &mdash; this "
              "is the documented program banks and payment processors require before onboarding. "
              "<strong>Banking and payment-processor introductions:</strong> direct introductions to Panamanian "
              "banks and crypto-friendly rails.",
              "<strong>Optional:</strong> a Private Interest Foundation (minimum endowment ~$10,000) for "
              "token-treasury or family-office holdings, and nominee director services where privacy matters."]),
            ("Ongoing Annual Cost: $5,000&ndash;$15,000",
             ["Annual maintenance covers the registered agent, the franchise tax, accounting and the ongoing "
              "upkeep of the compliance program. Because Panama taxes foreign-source income at 0%, there is no "
              "corporate income-tax drag on offshore revenue &mdash; a meaningful structural saving versus many "
              "onshore alternatives."]),
            ("Hidden Costs to Plan For",
             ["The two costs founders underestimate are <em>banking lead time</em> and <em>compliance "
              "documentation</em>. Panamanian banks tightened KYC after 2023; a thin file gets rejected and "
              "wastes weeks. Budget for a proper source-of-funds package up front. It is cheaper than a "
              "re-application."]),
        ],
        "faqs": [
            ("Is there a minimum capital requirement?",
             "No. A Panama Sociedad An&oacute;nima has no minimum paid-up capital, unlike many EU regimes."),
            ("Are nominee directors extra?",
             "Yes, nominee services are a separate annual line item. They are optional but common where founders "
             "want privacy on the public register."),
            ("Can you give a fixed quote?",
             "Yes. Once we understand your model and target markets we provide a fixed-fee proposal rather than "
             "an open-ended hourly arrangement."),
        ],
        "related": [
            ("Application process", "/application-process/"),
            ("Requirements checklist", "/requirements/"),
            ("Company setup", "/company-setup/"),
        ],
    },
    {
        "slug": "panama-crypto-license-requirements-checklist",
        "title": "Panama Crypto License Requirements: The 2026 Documentation Checklist",
        "keyword": "Panama crypto license requirements",
        "landing": "/requirements/",
        "labels": ["Panama", "Requirements", "Compliance"],
        "lede": "The single biggest cause of delay in a Panama crypto setup is incomplete paperwork. "
                "This is the exact documentation checklist we work through with clients before "
                "incorporation and banking.",
        "sections": [
            ("Corporate Documents",
             ["You will need passport copies and proof of address for every director and beneficial owner, "
              "a chosen company name (we check availability), and the intended business activity description. "
              "A Panama S.A. needs three directors; nominees are permitted where you prefer privacy.",
              f"The full intake list is on our <a href='{SITE}/requirements/'>requirements page</a>."]),
            ("AML/KYC Compliance Program",
             ["Banks and payment processors will not onboard a crypto business without a documented compliance "
              "program. This covers your KYC onboarding flow, transaction-monitoring rules, sanctions screening, "
              "a designated compliance officer, and record-keeping policies aligned with UAF Panama expectations.",
              "This is not a box-ticking PDF. It is the document that determines whether your banking application "
              "succeeds, so it is worth doing properly the first time."]),
            ("Source-of-Funds and Banking File",
             ["Expect to evidence the source of the company's funds and the personal wealth of beneficial owners. "
              "Since 2023, Panamanian banks scrutinise crypto-adjacent applicants closely. A clean, complete file "
              "moves through onboarding in 2&ndash;5 weeks; a thin one stalls."]),
            ("Ongoing Obligations",
             ["After setup you maintain the registered agent, pay the annual franchise tax, keep accounting "
              "records, and keep the compliance program live (periodic reviews, updated screening lists). "
              "We handle these on an annual retainer so nothing lapses."]),
        ],
        "faqs": [
            ("How many directors are required?",
             "Three. They can be non-resident, and nominee directors are permitted."),
            ("Do beneficial owners appear on a public register?",
             "Directors appear on the public register; using nominees keeps beneficial owners off it. Beneficial "
             "ownership is still disclosed to the registered agent under Panama's transparency rules."),
            ("How long does document collection take?",
             "Usually a few days if everyone responds promptly. It is the most controllable part of the timeline."),
        ],
        "related": [
            ("Cost breakdown", "/cost/"),
            ("Application process", "/application-process/"),
            ("Panama crypto license guide", "/"),
        ],
    },
    {
        "slug": "panama-crypto-exchange-license-explained",
        "title": "Setting Up a Crypto Exchange in Panama: License, Structure and Banking",
        "keyword": "Panama crypto exchange license",
        "landing": "/exchange-license/",
        "labels": ["Panama", "Exchange", "Crypto License"],
        "lede": "Running an exchange from Panama is entirely viable in 2026 &mdash; provided you understand "
                "that there is no named exchange license and that your real gating factor is banking "
                "and compliance, not a regulator badge.",
        "sections": [
            ("There Is No Named Exchange License",
             ["Because Panama has no dedicated VASP regime, you do not apply for an 'exchange license' as such. "
              "You incorporate a Sociedad An&oacute;nima, run the exchange under existing financial-services and "
              "AML law, and operate a compliance program supervised in spirit by UAF Panama.",
              f"Our <a href='{SITE}/exchange-license/'>exchange license page</a> walks through how this works in "
              "practice for order-book, brokerage and OTC models."]),
            ("Structuring the Operating Entity",
             ["Most exchange operators use a Panama S.A. as the operating company and, where there is a token or "
              "treasury, a Private Interest Foundation to hold it separately. Keeping operations and treasury in "
              "distinct vehicles is cleaner for both risk and banking.",
              "If you serve EU retail you will additionally need an EU-licensed entity under MiCA &mdash; Panama "
              "alone does not passport into Europe."]),
            ("Banking and Payment Rails",
             ["This is where exchanges live or die. You need fiat on/off-ramps, so the priority is securing a "
              "Panamanian bank account and crypto-friendly payment-processor relationships. We make direct "
              "introductions, but you must arrive with a complete compliance program and source-of-funds file. "
              "Panama's USD legal tender removes FX risk on USD settlement."]),
            ("Who This Suits",
             ["Panama exchanges work best for operators targeting Latin America and Asia, OTC desks serving HNW "
              "clients, and brokerages that do not need EU retail access. For a public CEX chasing EU customers, "
              "pair Panama with a Lithuania MiCA entity or start in Lithuania directly."]),
        ],
        "faqs": [
            ("Can I serve US customers from Panama?",
             "Not without separate US compliance. US money transmission needs state-by-state licensing or a "
             "FinCEN MSB registration; Panama does not cover it. Consider a Canada MSB or US setup for that."),
            ("Do I need a local Panamanian director?",
             "You need a registered agent in Panama and three directors who may be non-resident. We can supply "
             "nominees."),
            ("How long until I can take customers?",
             "Realistically 6&ndash;12 weeks once banking and the compliance program are in place."),
        ],
        "related": [
            ("Panama vs Lithuania", "/vs-lithuania/"),
            ("Company setup", "/company-setup/"),
            ("Requirements checklist", "/requirements/"),
        ],
    },
    {
        "slug": "panama-territorial-tax-crypto-business",
        "title": "Panama's Territorial Tax System: What It Means for a Crypto Business",
        "keyword": "Panama crypto tax",
        "landing": "/company-setup/",
        "labels": ["Panama", "Tax", "Crypto License"],
        "lede": "Panama's 0% tax on foreign-source income is the structural reason many crypto founders "
                "choose it. But the rule has nuance, and getting it wrong is expensive. Here is how "
                "territorial taxation actually works for a crypto company.",
        "sections": [
            ("How Territorial Taxation Works",
             ["Panama taxes income generated <em>within</em> Panama. Income from foreign sources &mdash; customers, "
              "trades and revenue arising outside Panama &mdash; is taxed at 0%. For an offshore-facing crypto "
              "business serving Latin America, Asia or global HNW clients, the bulk of revenue is foreign-source.",
              "Combined with the US dollar as legal tender (1:1 with the balboa), this gives a USD-denominated "
              "crypto operation a clean, low-friction base with no FX exposure on settlement."]),
            ("Where Founders Get It Wrong",
             ["The 0% rate applies to <em>foreign-source</em> income, not automatically to everything. Revenue "
              "with a genuine Panamanian nexus &mdash; local customers, local operations &mdash; can be taxable. "
              "Mischaracterising income source is the classic mistake. Document where value is actually generated.",
              "Your home country's tax residency rules also still apply to you personally. A Panama company does "
              "not erase your individual tax obligations where you live. This is why we introduce qualified tax "
              "advisors as part of every setup."]),
            ("Substance and Reputation",
             ["Post-FATF-grey-list (Panama exited in October 2023), substance matters more than it used to. "
              "Banks and counterparties increasingly want to see real operational substance, not just a shell. "
              "Plan for genuine management, record-keeping and a credible compliance function.",
              f"Our <a href='{SITE}/company-setup/'>company setup</a> guidance covers building appropriate "
              "substance from day one."]),
            ("The Net Effect",
             ["For the right business &mdash; offshore-facing, USD-settled, not chasing EU retail &mdash; Panama's "
              "territorial system is a legitimate and meaningful efficiency. For an EU-retail exchange, the tax "
              "saving rarely outweighs the lack of a MiCA passport."]),
        ],
        "faqs": [
            ("Is the 0% rate a loophole?",
             "No. Territorial taxation is Panama's longstanding, lawful system. The key is correctly classifying "
             "foreign-source versus Panamanian-source income."),
            ("Do I still pay tax at home?",
             "Likely yes, depending on your personal tax residency. A Panama company does not remove your "
             "individual obligations. Take local advice."),
            ("Is there VAT on crypto services?",
             "Panama's ITBMS (its VAT equivalent) generally applies to services consumed in Panama. Foreign-facing "
             "services are typically outside its scope, but confirm specifics with counsel."),
        ],
        "related": [
            ("Cost breakdown", "/cost/"),
            ("Panama crypto license guide", "/"),
            ("Requirements checklist", "/requirements/"),
        ],
    },
    {
        "slug": "panama-private-interest-foundation-crypto-treasury",
        "title": "Panama Private Interest Foundation: The Crypto Treasury Structure Explained",
        "keyword": "Panama foundation crypto treasury",
        "landing": "/company-setup/",
        "labels": ["Panama", "Foundation", "Treasury", "DAO"],
        "lede": "Token treasuries, DAO foundations and family-office crypto holdings need a structure "
                "that separates assets from operations. In Panama, that structure is the Private "
                "Interest Foundation. Here is how it is used in crypto.",
        "sections": [
            ("What a Private Interest Foundation Is",
             ["A Panama Private Interest Foundation is an orphan legal entity with no shareholders &mdash; it owns "
              "itself and is governed by a foundation charter and a council. It is built for asset protection "
              "and succession, which makes it well suited to holding a token treasury or long-term crypto "
              "reserves separate from any operating company.",
              "The minimum endowment is roughly $10,000. It is frequently paired with an operating Sociedad "
              "An&oacute;nima: the S.A. runs the business, the foundation holds the treasury."]),
            ("Why DAOs and Token Projects Use It",
             ["A foundation can act as the legal wrapper for a DAO &mdash; signing contracts, holding the treasury, "
              "and providing a point of legal responsibility that a purely on-chain DAO lacks. Because it has no "
              "owners, it aligns with the ownerless ethos of a DAO while still being able to interface with banks, "
              "exchanges and counterparties.",
              f"We cover wrapper options in our <a href='{SITE}/company-setup/'>company setup</a> guidance."]),
            ("Asset Protection and Succession",
             ["Assets endowed to the foundation are legally separated from the founder's personal estate, which "
              "provides protection and a clear succession path defined in the charter. For family offices holding "
              "significant crypto, this separation is the entire point."]),
            ("Practical Considerations",
             ["A foundation still needs a registered agent, a council, and &mdash; for banking &mdash; the same "
              "compliance and source-of-funds rigour as any other crypto-adjacent applicant. It is not a way to "
              "avoid KYC; it is a way to structure ownership and protection cleanly."]),
        ],
        "faqs": [
            ("Can a foundation trade actively?",
             "It can hold and manage assets, but active trading or customer-facing operations usually belong in "
             "an operating S.A. The common pattern is foundation-holds, company-operates."),
            ("Who controls the foundation?",
             "A council, guided by the charter and optional by-laws. The founder can retain influence through the "
             "charter while keeping legal separation."),
            ("What is the minimum endowment?",
             "Around $10,000. This is the asset base the foundation is established with."),
        ],
        "related": [
            ("Panama crypto license guide", "/"),
            ("Cost breakdown", "/cost/"),
            ("Requirements checklist", "/requirements/"),
        ],
    },
    {
        "slug": "panama-crypto-banking-guide-2026",
        "title": "Banking a Panama Crypto Company in 2026: How to Get Approved",
        "keyword": "Panama crypto banking",
        "landing": "/application-process/",
        "labels": ["Panama", "Banking", "Compliance"],
        "lede": "Incorporation is the easy part. Banking is where most Panama crypto setups stall. "
                "Here is what Panamanian banks actually want to see in 2026 and how to get approved "
                "the first time.",
        "sections": [
            ("Why Banking Is the Hard Part",
             ["Since 2023, Panamanian banks have tightened KYC for crypto-adjacent businesses, partly in response "
              "to FATF scrutiny (Panama exited the grey list in October 2023). Banks now expect a complete, "
              "professional application. A thin file is rejected, and re-applying wastes weeks.",
              f"Our <a href='{SITE}/application-process/'>application process</a> sequences incorporation and "
              "banking so the file is ready when you approach the bank."]),
            ("What the Bank Wants to See",
             ["A documented AML/KYC compliance program with a named compliance officer. A clear, evidenced "
              "source-of-funds for both the company and beneficial owners. A coherent business description "
              "explaining who your customers are and how money moves. And realistic projected volumes.",
              "The narrative matters as much as the documents: banks approve businesses they understand."]),
            ("Timeline and Sequencing",
             ["Expect 2&ndash;5 weeks for banking onboarding once the file is complete. Sequencing is everything: "
              "incorporate the S.A., build the compliance program, assemble the source-of-funds package, then "
              "approach the bank with introductions in hand. Approaching banks cold, mid-setup, is the most "
              "common self-inflicted delay."]),
            ("Payment Processors and Fiat Rails",
             ["Alongside a bank account, crypto-friendly payment processors give you usable fiat on/off-ramps. "
              "We make direct introductions to rails that work with Panama-incorporated crypto businesses. "
              "Panama's USD legal tender means no FX conversion friction on USD settlement."]),
        ],
        "faqs": [
            ("Can you guarantee a bank account?",
             "No reputable advisor can guarantee a bank decision. What we do is maximise approval odds with a "
             "complete file and the right introductions &mdash; which is the difference between approval and "
             "rejection in practice."),
            ("How many banks should I apply to?",
             "Usually we target the best-fit introductions first rather than spraying applications, which can "
             "harm your profile. Quality of file beats quantity of applications."),
            ("Do payment processors need the same documents?",
             "Largely yes &mdash; the same compliance program and source-of-funds file serves both bank and "
             "processor onboarding."),
        ],
        "related": [
            ("Requirements checklist", "/requirements/"),
            ("Cost breakdown", "/cost/"),
            ("Exchange license options", "/exchange-license/"),
        ],
    },
]

# ── keyword-driven generator (other jurisdictions) ───────────────────────────
# Facts are best-effort 2026 ranges and general guidance, not legal advice
# (every article carries the disclaimer). Panama is hand-authored above; this
# generator covers the other jurisdictions Consulting24 serves and always
# links back to consulting24.co landing pages.

YEAR = 2026
PANAMA_COST = "$15,000–$45,000"
PANAMA_TIME = "6–12 weeks"

JURISDICTIONS: list[dict] = [
    {"name": "Lithuania", "slug": "lithuania",
     "regime": "EU MiCA CASP authorisation (transitioned from the old VASP register)",
     "authority": "the Bank of Lithuania",
     "cost": "$50,000–$120,000", "timeline": "4–8 months",
     "tax": "15% corporate income tax, with reliefs for small companies",
     "region": "the European Union",
     "best_for": "exchanges and wallets that need to serve EU retail customers under a MiCA passport",
     "not_for": "founders who only need an offshore base and have no EU retail ambitions",
     "note": "Lithuania absorbed most operators who left Estonia after the 2024 crackdown and is now the default EU crypto base."},
    {"name": "Dubai (VARA)", "slug": "dubai-vara",
     "regime": "a VARA virtual-asset licence (with ADGM and DFSA as alternative routes)",
     "authority": "the Virtual Assets Regulatory Authority (VARA)",
     "cost": "$100,000+ all-in", "timeline": "6–12 months",
     "tax": "0% personal income tax and 9% corporate tax above the threshold",
     "region": "the UAE and wider MENA region",
     "best_for": "institutional and MENA-facing exchanges that want a top-tier regulator badge",
     "not_for": "early-stage projects on a tight budget",
     "note": "VARA is rigorous and expensive but carries strong international credibility."},
    {"name": "Canada (MSB)", "slug": "canada-msb",
     "regime": "a FINTRAC money-services-business (MSB) registration",
     "authority": "FINTRAC",
     "cost": "$8,000–$25,000", "timeline": "3–6 weeks",
     "tax": "standard Canadian corporate tax",
     "region": "North America",
     "best_for": "crypto-to-fiat exchanges that need North American fiat rails",
     "not_for": "businesses targeting EU retail, since there is no MiCA passport",
     "note": "Fast, affordable and credible for North-American-facing operations."},
    {"name": "BVI", "slug": "bvi",
     "regime": "registration under the BVI VASP Act 2022",
     "authority": "the BVI Financial Services Commission",
     "cost": "$25,000–$60,000", "timeline": "8–16 weeks",
     "tax": "0% on corporate income",
     "region": "the Caribbean offshore market",
     "best_for": "offshore operators who want more legal certainty than a pure-offshore shell",
     "not_for": "businesses needing EU retail access",
     "note": "A stronger statutory framework than many pure-offshore alternatives since the 2022 VASP Act."},
    {"name": "Estonia", "slug": "estonia",
     "regime": "VASP authorisation, now folded into the EU MiCA regime",
     "authority": "the Estonian FIU",
     "cost": "$30,000–$70,000", "timeline": "4–6 months",
     "tax": "0% on retained profits and 20% on distributions",
     "region": "the European Union",
     "best_for": "operators with existing Estonian substance",
     "not_for": "new entrants — most now migrate to Lithuania",
     "note": "The 2024 crackdown sharply reduced Estonia's appeal; approach with caution."},
    {"name": "El Salvador", "slug": "el-salvador",
     "regime": "a Digital Asset Service Provider (DASP) registration under the Bitcoin Law framework",
     "authority": "the National Digital Assets Commission (CNAD)",
     "cost": "$30,000–$100,000", "timeline": "2–5 months",
     "tax": "0% on digital-asset gains",
     "region": "Latin America",
     "best_for": "Bitcoin-native and LATAM-facing businesses",
     "not_for": "businesses needing an EU passport",
     "note": "Bitcoin is legal tender; the framework is pioneering but still young."},
    {"name": "Switzerland", "slug": "switzerland",
     "regime": "FINMA authorisation or SRO membership",
     "authority": "FINMA",
     "cost": "$80,000–$200,000", "timeline": "4–9 months",
     "tax": "competitive cantonal corporate rates",
     "region": "Europe (non-EU)",
     "best_for": "high-credibility token issuers and institutional players",
     "not_for": "budget-constrained startups",
     "note": "The Zug 'Crypto Valley' ecosystem gives Switzerland a premium reputation."},
    {"name": "Malta", "slug": "malta",
     "regime": "MiCA CASP authorisation (formerly the VFA Act)",
     "authority": "the MFSA",
     "cost": "$40,000–$90,000", "timeline": "4–8 months",
     "tax": "a low effective rate via Malta's refund system",
     "region": "the European Union",
     "best_for": "EU-facing operators who want an established crypto-friendly regulator",
     "not_for": "those chasing the lowest possible cost",
     "note": "An early mover ('Blockchain Island'), now operating under MiCA."},
    {"name": "Cayman Islands", "slug": "cayman",
     "regime": "registration or licensing under the Cayman VASP Act",
     "authority": "the Cayman Islands Monetary Authority (CIMA)",
     "cost": "$30,000–$80,000", "timeline": "3–6 months",
     "tax": "0% on corporate income",
     "region": "the Caribbean offshore market",
     "best_for": "crypto funds and institutional vehicles",
     "not_for": "low-budget startups",
     "note": "Particularly favoured by crypto funds and structured vehicles."},
    {"name": "Czech Republic", "slug": "czech-republic",
     "regime": "EU MiCA CASP authorisation (historically a light-touch trade licence)",
     "authority": "the Czech National Bank",
     "cost": "$15,000–$40,000", "timeline": "2–4 months",
     "tax": "19% corporate income tax",
     "region": "the European Union",
     "best_for": "cost-sensitive operators who want an EU base",
     "not_for": "those needing a premium regulator badge",
     "note": "Historically one of the cheapest EU routes; tightening under MiCA."},
    {"name": "Poland", "slug": "poland",
     "regime": "EU MiCA CASP authorisation (from the former VASP register)",
     "authority": "the Polish Financial Supervision Authority (KNF)",
     "cost": "$15,000–$45,000", "timeline": "2–5 months",
     "tax": "19% corporate income tax",
     "region": "the European Union",
     "best_for": "cost-sensitive EU operators",
     "not_for": "premium-badge seekers",
     "note": "An affordable EU base now transitioning fully to MiCA."},
    {"name": "Georgia", "slug": "georgia",
     "regime": "VASP registration, with free-industrial-zone options",
     "authority": "the National Bank of Georgia",
     "cost": "$10,000–$30,000", "timeline": "3–8 weeks",
     "tax": "0% inside the free industrial zones",
     "region": "the Eurasia region",
     "best_for": "a low-cost, fast offshore-style base outside the EU",
     "not_for": "businesses needing EU retail access or top-tier recognition",
     "note": "Cheap and fast, but with lower international recognition than EU or major offshore hubs."},
    {"name": "Seychelles", "slug": "seychelles",
     "regime": "registration under the Seychelles VASP Act 2024",
     "authority": "the Financial Services Authority (FSA)",
     "cost": "$15,000–$40,000", "timeline": "6–12 weeks",
     "tax": "0% on foreign-source income",
     "region": "the offshore market",
     "best_for": "offshore exchanges and token projects on a budget",
     "not_for": "EU retail or premium-badge needs",
     "note": "A popular budget offshore option, newly formalised by the 2024 VASP Act."},
]

# Internal landing page per angle (all real consulting24.co pages).
_ANGLE_LANDING = {
    "guide": "/",
    "cost": "/cost/",
    "requirements": "/requirements/",
    "vs-panama": "/vs-lithuania/",
}

def _related_for(angle: str) -> list[tuple[str, str]]:
    base = [
        ("Panama crypto license guide", "/"),
        ("Cost breakdown", "/cost/"),
        ("Panama vs Lithuania", "/vs-lithuania/"),
        ("Requirements checklist", "/requirements/"),
        ("Application process", "/application-process/"),
        ("Exchange license options", "/exchange-license/"),
    ]
    # rotate so related lists differ a little per angle
    order = {"guide": 0, "cost": 1, "requirements": 3, "vs-panama": 2}.get(angle, 0)
    rotated = base[order:] + base[:order]
    return rotated[:3]

def _gen_guide(j: dict) -> dict:
    n = j["name"]
    return {
        "slug": f"{j['slug']}-crypto-license-{YEAR}-guide",
        "title": f"{n} Crypto License {YEAR}: Cost, Requirements and Timeline",
        "keyword": f"{n} crypto license",
        "labels": [n.split(" (")[0], "Crypto License", "Guide"],
        "lede": f"Thinking about a {n} crypto license? Here is a clear {YEAR} overview of the "
                f"regime, what it costs, how long it takes, and whether {n} is the right base for "
                f"your business — with an honest comparison to Panama.",
        "sections": [
            (f"How {n} Regulates Crypto",
             [f"{n} works through {j['regime']}, supervised by {j['authority']}. {j['note']}",
              f"Whether that fits depends on your customers and goals. {n} is generally the right "
              f"choice for {j['best_for']}, and a poor fit for {j['not_for']}."]),
            ("Cost and Timeline",
             [f"Budget roughly {j['cost']} to set up in {n}, with a realistic timeline of {j['timeline']}. "
              f"By comparison, a Panama Sociedad An&oacute;nima sets up in {PANAMA_TIME} for {PANAMA_COST} all-in "
              f"the first year — faster and cheaper, but without an EU passport.",
              f"See our <a href='{SITE}/cost/'>cost breakdown</a> for how Panama's line items compare, and "
              f"our <a href='{SITE}/application-process/'>application process</a> for the end-to-end steps."]),
            ("Tax and Banking",
             [f"On tax, {n} applies {j['tax']}. Banking, as everywhere in crypto, is the real gating factor: "
              f"expect to present a documented AML/KYC program and a clean source-of-funds file before any "
              f"bank or payment processor will onboard you.",
              f"Panama, by contrast, taxes foreign-source income at 0% and uses the US dollar as legal tender, "
              f"which removes FX risk on USD settlement — one reason offshore-facing operators shortlist it."]),
            (f"Is {n} Right for You?",
             [f"Choose {n} if your priority is {j['best_for']}. Look elsewhere if you are {j['not_for']}.",
              f"If you are weighing {n} against an offshore base, read our "
              f"<a href='{SITE}/vs-lithuania/'>Panama vs Lithuania</a> comparison — the same decision "
              f"framework applies, and we are happy to map it to {n} for your specific model."]),
        ],
        "faqs": [
            (f"How much does a {n} crypto license cost?",
             f"Roughly {j['cost']} to set up, plus ongoing annual maintenance. The range depends on scope — "
             f"compliance program, banking introductions and any nominee or substance requirements."),
            (f"How long does {n} take?",
             f"Around {j['timeline']} end to end, assuming a complete application. Incomplete documentation is "
             f"the most common cause of delay anywhere."),
            (f"Is {n} better than Panama?",
             f"It depends on your customers. {n} suits {j['best_for']}; Panama wins on speed, cost and "
             f"territorial-tax efficiency for offshore-facing businesses. We help clients choose objectively."),
        ],
    }

def _gen_cost(j: dict) -> dict:
    n = j["name"]
    return {
        "slug": f"{j['slug']}-crypto-license-cost",
        "title": f"How Much Does a {n} Crypto License Cost in {YEAR}?",
        "keyword": f"{n} crypto license cost",
        "labels": [n.split(" (")[0], "Cost", "Crypto License"],
        "lede": f"Quotes for a {n} crypto license vary widely because providers bundle different things. "
                f"Here is an honest view of what it actually costs in {YEAR} — and how that stacks up "
                f"against Panama.",
        "sections": [
            (f"The Headline Number: {j['cost']}",
             [f"A {n} setup typically runs {j['cost']} in the first year. That covers {j['regime']} via "
              f"{j['authority']}, plus the compliance and corporate work around it. {j['note']}",
              f"Panama, for comparison, is {PANAMA_COST} all-in for year one — useful as a price anchor when "
              f"you read a {n} quote. See our <a href='{SITE}/cost/'>full cost breakdown</a>."]),
            ("What Drives the Cost",
             [f"The big cost drivers are the same everywhere: the licensing/registration fees, a documented "
              f"AML/KYC compliance program, banking and payment-processor onboarding, and any nominee or local "
              f"substance requirements. In {n}, the {j['regime'].split('(')[0].strip()} is the largest single line.",
              "A thin compliance file is a false economy — it gets rejected at the banking stage and costs you "
              "weeks. Budget for it properly up front."]),
            ("Ongoing Annual Cost",
             [f"On top of setup, plan for annual maintenance: renewal/supervision fees, accounting, and keeping "
              f"the compliance program live. Tax treatment matters too — {n} applies {j['tax']}, versus Panama's "
              f"0% on foreign-source income.",
              f"Our <a href='{SITE}/requirements/'>requirements checklist</a> shows what you maintain after "
              f"go-live so nothing lapses."]),
            ("Getting an Honest Quote",
             [f"Ask any provider to itemise: incorporation, licence/registration, compliance program, banking "
              f"introductions, and year-two maintenance. Open-ended hourly arrangements are where {n} budgets "
              f"overrun.",
              "Consulting24 provides fixed-fee proposals once we understand your model and target markets, so "
              "you know the all-in number before you commit."]),
        ],
        "faqs": [
            (f"What is the cheapest way to get a {n} crypto license?",
             f"Keep scope tight, but never cut the compliance program — that is what unlocks banking. Expect at "
             f"least the lower end of {j['cost']}."),
            ("Are there hidden costs?",
             "The two most underestimated are banking lead time and compliance documentation. Both are "
             "controllable with a complete file."),
            ("How does this compare to Panama?",
             f"Panama is {PANAMA_COST} for year one in {PANAMA_TIME}, with 0% tax on foreign-source income — "
             f"often the cheaper, faster route for offshore-facing businesses."),
        ],
    }

def _gen_requirements(j: dict) -> dict:
    n = j["name"]
    return {
        "slug": f"{j['slug']}-crypto-license-requirements",
        "title": f"{n} Crypto License Requirements: {YEAR} Checklist",
        "keyword": f"{n} crypto license requirements",
        "labels": [n.split(" (")[0], "Requirements", "Compliance"],
        "lede": f"Incomplete paperwork is the number-one cause of delay in any crypto licensing project. "
                f"Here is what {n} actually requires in {YEAR}, and how to assemble a file that gets "
                f"approved the first time.",
        "sections": [
            ("Corporate and Licensing Requirements",
             [f"To operate in {n} you work through {j['regime']}, supervised by {j['authority']}. That means a "
              f"local operating entity, fit-and-proper directors, and a clearly described business activity.",
              f"{j['note']} We confirm the current requirements with local counsel for every engagement, since "
              f"crypto rules change frequently."]),
            ("AML/KYC Compliance Program",
             ["No bank or payment processor will onboard a crypto business without a documented compliance "
              "program: a KYC onboarding flow, transaction monitoring, sanctions screening, a designated "
              "compliance officer, and record-keeping policies.",
              f"This is the document that determines whether banking succeeds in {n}, so it is worth doing "
              f"properly. Our <a href='{SITE}/requirements/'>requirements checklist</a> shows the full intake."]),
            ("Documentation and Timeline",
             [f"Expect to evidence source of funds for the company and beneficial owners, plus standard KYC on "
              f"directors. With a complete file, {n} runs about {j['timeline']}.",
              f"Sequencing matters: incorporate, build the compliance program, assemble the source-of-funds "
              f"package, then approach banking with introductions in hand."]),
            ("Common Pitfalls",
             [f"The usual failures are a thin compliance program, an unexplained source of funds, and approaching "
              f"banks cold mid-setup. Each one costs weeks.",
              f"If {n}'s requirements feel heavy for your stage, Panama is a lighter, faster alternative for "
              f"offshore-facing businesses — see our <a href='{SITE}/'>Panama crypto license guide</a>."]),
        ],
        "faqs": [
            (f"What documents do I need for {n}?",
             "Passports and proof of address for directors and beneficial owners, a business description, and a "
             "documented AML/KYC program with source-of-funds evidence."),
            ("Do I need a local director?",
             f"Requirements vary by jurisdiction; some need local substance. We confirm {n}'s current rules with "
             f"local counsel and arrange what is needed."),
            ("What slows applications down most?",
             "Incomplete documentation and a weak compliance file. Both are within your control."),
        ],
    }

def _gen_vs_panama(j: dict) -> dict:
    n = j["name"]
    return {
        "slug": f"{j['slug']}-vs-panama-crypto-license",
        "title": f"{n} vs Panama for a Crypto License: Which Should You Choose?",
        "keyword": f"{n} vs Panama crypto license",
        "labels": [n.split(" (")[0], "Panama", "Comparison"],
        "lede": f"Should you license in {n} or Panama? The right answer depends entirely on who your "
                f"customers are. Here is the decision framework we use with clients.",
        "sections": [
            ("The Core Trade-off",
             [f"{n} works through {j['regime']} ({j['authority']}), costs about {j['cost']}, and takes "
              f"{j['timeline']}. Panama uses a Sociedad An&oacute;nima with no dedicated VASP regime, costs "
              f"{PANAMA_COST}, and takes {PANAMA_TIME}.",
              f"In short: {n} typically buys you regulatory standing in {j['region']}; Panama buys you speed, "
              f"low cost and 0% tax on foreign-source income."]),
            (f"When {n} Wins",
             [f"Pick {n} if your priority is {j['best_for']}. {j['note']}",
              f"On tax, {n} applies {j['tax']} — factor that into the total cost of ownership, not just the "
              f"setup fee."]),
            ("When Panama Wins",
             ["Panama wins for offshore-first operations that do not need an EU or onshore passport: businesses "
              "targeting Latin America, Asia or HNW clients, founders who value fast incorporation, and anyone "
              "prioritising territorial-tax efficiency.",
              f"It is the wrong choice if you specifically need {n}'s market access or regulator badge — be "
              f"honest with yourself about which you actually require."]),
            ("How to Decide",
             [f"Map it to customers first, cost second. If you need {j['region']} access, lean {n}. If you are "
              f"offshore-facing and want to move fast, lean Panama.",
              f"Our <a href='{SITE}/vs-lithuania/'>Panama vs Lithuania</a> page lays out the same logic in "
              f"detail, and we will happily map it to {n} for your exact model."]),
        ],
        "faqs": [
            (f"Is {n} more expensive than Panama?",
             f"Generally yes — {n} runs {j['cost']} versus Panama at {PANAMA_COST}. You pay for {n}'s market "
             f"access and regulatory standing."),
            ("Can I start in Panama and move later?",
             f"Yes. Many founders launch offshore in Panama to validate the business, then add a {n} entity once "
             f"revenue justifies the cost and the market access is needed."),
            (f"Which is faster, {n} or Panama?",
             f"Panama, almost always — {PANAMA_TIME} versus {j['timeline']} for {n}."),
        ],
    }

_GENERATORS = {
    "guide": _gen_guide, "cost": _gen_cost,
    "requirements": _gen_requirements, "vs-panama": _gen_vs_panama,
}

def _generate() -> list[dict]:
    out = []
    for j in JURISDICTIONS:
        for angle, fn in _GENERATORS.items():
            topic = fn(j)
            topic["landing"] = _ANGLE_LANDING[angle]
            topic["related"] = _related_for(angle)
            out.append(topic)
    return out

# Final queue: hand-authored Panama articles first, then generated coverage.
ARTICLES: list[dict] = PANAMA_ARTICLES + _generate()

# ── posting ───────────────────────────────────────────────────────────────

def insert_post(blogger, blog_id: str, topic: dict, dry_run: bool) -> dict:
    html = render_article(topic)
    body = {
        "kind": "blogger#post",
        "blog": {"id": blog_id},
        "title": topic["title"],
        "content": html,
        "labels": topic.get("labels", []),
    }
    if dry_run:
        log(f"[dry-run] would publish '{topic['title']}' ({len(html)} chars, "
            f"{len(topic['labels'])} labels)")
        return {"id": "(dry-run)", "url": f"{SITE}{topic['landing']}"}
    resp = blogger.posts().insert(blogId=blog_id, body=body, isDraft=False).execute()
    return resp

def next_unposted(state: dict) -> list[dict]:
    return [a for a in ARTICLES if not posted(state, a["slug"])]

def cmd_list(state: dict):
    done = set(state.get("posts", {}).keys())
    print(f"\nArticles: {len(ARTICLES)} total, {len(done)} posted, "
          f"{len(ARTICLES) - len(done)} remaining\n")
    for a in ARTICLES:
        mark = "✓" if a["slug"] in done else " "
        url = state.get("posts", {}).get(a["slug"], {}).get("url", "")
        print(f"  [{mark}] {a['slug']}{('  → ' + url) if url else ''}")
    print()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--login", action="store_true", help="run OAuth as mardo@consulting24.co and exit")
    ap.add_argument("--list", action="store_true", help="show queue + posted state and exit")
    ap.add_argument("--dry-run", action="store_true", help="render next post without publishing")
    ap.add_argument("--once", metavar="SLUG", help="publish one specific article slug")
    ap.add_argument("--limit", type=int, default=DAILY_LIMIT)
    args = ap.parse_args()

    state = load_state()

    if args.list:
        cmd_list(state)
        return

    if args.login:
        get_credentials()
        log(f"OAuth complete. Token saved to {TOKEN_PATH}")
        return

    blog_id = require_env("BLOGGER_BLOG_ID")

    creds = get_credentials()
    blogger = build_blogger(creds)

    # confirm blog access early
    try:
        info = blogger.blogs().get(blogId=blog_id).execute()
        log(f"Connected to blog: {info.get('name')} ({info.get('url')})")
    except Exception as e:
        sys.exit(f"ERROR: cannot access BLOGGER_BLOG_ID={blog_id}: {e}")

    if args.once:
        topic = next((a for a in ARTICLES if a["slug"] == args.once), None)
        if not topic:
            sys.exit(f"ERROR: no article with slug '{args.once}'")
        targets = [topic]
    else:
        targets = next_unposted(state)[: args.limit]

    if not targets:
        log("Nothing to publish — all articles posted.")
        return

    for topic in targets:
        try:
            resp = insert_post(blogger, blog_id, topic, args.dry_run)
            if not args.dry_run:
                mark_posted(state, topic["slug"], {
                    "title": topic["title"], "url": resp.get("url", ""),
                    "post_id": resp.get("id", ""),
                })
                save_state(state)
                log(f"Published: {topic['title']} → {resp.get('url','')}")
        except Exception as e:
            log(f"ERROR publishing {topic['slug']}: {e}")
            log(traceback.format_exc())

if __name__ == "__main__":
    main()
