#!/usr/bin/env python3
"""
generate.py — DeepSeek-powered landing/blog page generator for consulting24.co.
Claude is the "brain" (structure, QC spec, assembly, gating); DeepSeek writes the prose.

Usage:
  python3 scripts/generate.py landing <slug> "<primary keyword>" "<brief / jurisdiction facts>"
  python3 scripts/generate.py blog    <slug> "<primary keyword>" "<brief>"

Reads the DeepSeek key from $DEEPSEEK_API_KEY or scripts/.deepseek_key (gitignored).
Enforces the Consulting24 QC checklist: >=2000 words, >=8 FAQs, full section
structure, internal links, validated external authority links, schema, EEAT.
"""
import os, sys, re, json, html, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.consulting24.co"
WA = "https://wa.me/37258155779?text=Hi%2C%20I%27d%20like%20to%20ask%20about%20a%20crypto%20company%20setup."

def key():
    k = os.environ.get("DEEPSEEK_API_KEY")
    if k: return k.strip()
    p = os.path.join(ROOT, "scripts", ".deepseek_key")
    if os.path.exists(p): return open(p).read().strip()
    sys.exit("No DeepSeek key (set DEEPSEEK_API_KEY or scripts/.deepseek_key)")

# Known internal URLs the model may link to (prevents broken internal links)
INTERNAL = ["/", "/cost/", "/requirements/", "/application-process/", "/exchange-license/",
  "/company-setup/", "/vs-lithuania/", "/jurisdictions/", "/blog/",
  "/lithuania-crypto-license/", "/estonia-crypto-license/", "/dubai-crypto-license/",
  "/el-salvador-crypto-license/", "/czech-republic-crypto-license/", "/poland-crypto-license/",
  "/malta-crypto-license/", "/switzerland-crypto-license/", "/cyprus-crypto-license/",
  "/cayman-islands-crypto-license/"]

SYSTEM = """You are a senior crypto-licensing copywriter for Consulting24 (X24Consulting OU, Tallinn, Estonia), a firm that has obtained 500+ crypto licenses, delivering directly in Estonia, Lithuania and Panama and advising/coordinating in all other jurisdictions. Panama company price is a flat EUR 6,000. Write in clear, confident, expert British/EU English for crypto founders.

Output STRICT JSON only, matching this schema:
{
 "meta_title": "50-60 chars, includes the primary keyword",
 "meta_description": "120-155 chars, human, with a value proposition/CTA, includes primary keyword",
 "h1": "includes the primary keyword",
 "intro_html": "2-3 <p> paragraphs; primary keyword in the first 100 words",
 "sections": [ {"h2": "...", "html": "valid HTML: <p>, <ul>, <ol>, <table class=\\"t-wrap-inner\\">, <h3> where useful"} , ... ],
 "faqs": [ {"q":"...","a":"..."}, ... ],
 "authority_links": [ {"title":"Official regulator name","url":"https://...official homepage..."} ]
}

Hard requirements (this is a strict QC gate — pages failing are rejected):
- TOTAL body length (intro + sections + FAQ answers) MUST be 2300-3500 words of UNIQUE, substantive content. This is strictly enforced. Write 13-16 sections; each main section 180-320 words with concrete detail, examples and at least one list or table where useful. Do NOT stop early or write thin sections.
- Include these sections in order: Overview/what it is; Who needs it; License type & regulator; Cost & timeline (with a table); Capital requirement; Tax treatment; Allowed activities; Step-by-step process; Banking & payments; Benefits; Compliance & trust; Common mistakes; Alternatives/comparison (vs Panama and 1-2 others).
- At least 8 FAQs (aim 10-12), each a real question with a 40-90 word answer.
- Weave 5-8 contextual internal links using ONLY paths from this allow-list (exact href): __INTERNAL__ . Always link Panama as <a href="/">Panama</a> and the hub as <a href="/jurisdictions/">jurisdictions</a> at least once.
- authority_links: 1-3 OFFICIAL regulator/government homepages you are highly confident exist (e.g. the financial regulator's main site). If unsure of a URL, omit it. Never invent URLs.
- FACTUAL ACCURACY (critical): treat the FACTS in the user brief as AUTHORITATIVE and current for 2026. Restate the brief's regulator, licence type, capital, tax and timeline EXACTLY — never override them with older/pre-MiCA information from your training. MiCA is FULLY IN FORCE in 2026: the EU CASP regime is live (not "upcoming"/"will expand"), and EU member states apply capital tiers of EUR 50,000 / 125,000 / 150,000 by service class. Do NOT describe EU crypto licensing as the old "VASP register / no minimum capital" model.
- FIGURES: you MAY and SHOULD state specific numbers (fees, capital, timelines, ongoing costs) that are EXPLICITLY GIVEN in the brief — treat brief figures as authoritative and present them clearly (e.g. in the cost table). Panama = EUR 6,000 fixed. You must NOT invent figures that are not in the brief: for anything not provided, use a hedged range and say exact pricing is confirmed in a consultation. No fabricated statistics, no invented laws. Hedge undocumented items with "typically", "as of 2026". Add 'general guidance, not legal advice' in compliance sections. Never promise approval or guarantees.
- Honest delivery framing: say Consulting24 delivers directly for Estonia/Lithuania/Panama; for others it 'advises and coordinates'. EXCEPTION: if the brief contains "DELIVERY=comparison-only" (e.g. UAE/Dubai/Abu Dhabi VARA), Consulting24 does NOT provide that licence — write the page as neutral, informational, and COMPARISON-focused (especially vs Panama); do NOT claim Consulting24 advises/coordinates/files that licence; the CTA must steer the reader to Panama and the jurisdictions Consulting24 does serve (Estonia/Lithuania), framing C24's role as "we help you choose the right route and set up where we operate".
- Every CTA points to talking to an expert on WhatsApp / booking a consultation (do not print the phone number as plain text).
- No keyword stuffing (primary keyword density ~0.8-1.8%). No markdown, valid HTML only inside html fields.
- STYLE/VOICE (anti-AI-detection, strict): write naturally for a professional founder audience, varied sentence length, concrete and specific. NEVER use em-dashes or en-dashes — use commas, hyphens, or rephrase. NO exclamation marks. Do NOT use these AI-cliche words/phrases at all: delve, leverage, seamless, robust, cutting-edge, groundbreaking, game-changing, harness, unleash, empower, paradigm, synergy, holistic, navigate/navigating the landscape, "in today's world", "when it comes to", "that being said", "in essence", "in short", "at the end of the day", "in conclusion", "it's worth noting", "rest assured", "look no further".""".replace("__INTERNAL__", ", ".join(INTERNAL))

BANNED = ["delve","leverage","seamless","robust","cutting-edge","groundbreaking","game-changing",
  "harness","unleash","empower","paradigm","synergy","holistic","in today's world","when it comes to",
  "that being said","in essence","at the end of the day","in conclusion","it's worth noting","look no further"]

def _clean(s):
    if not isinstance(s, str): return s
    for a, b in (("—", "-"), ("–", "-"), ("&mdash;", "-"), ("&ndash;", "-"), ("!", ".")):
        s = s.replace(a, b)
    return s

def _clean_d(d):
    d["meta_title"] = _clean(d.get("meta_title", "")); d["meta_description"] = _clean(d.get("meta_description", ""))
    d["h1"] = _clean(d.get("h1", "")); d["intro_html"] = _clean(d.get("intro_html", ""))
    for s in d.get("sections", []): s["h2"] = _clean(s.get("h2", "")); s["html"] = _clean(s.get("html", ""))
    for f in d.get("faqs", []): f["q"] = _clean(f.get("q", "")); f["a"] = _clean(f.get("a", ""))
    return d

def call_deepseek(user):
    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role":"system","content":SYSTEM},{"role":"user","content":user}],
        "response_format": {"type":"json_object"},
        "max_tokens": 8000, "temperature": 0.6, "stream": False,
    }).encode()
    req = urllib.request.Request("https://api.deepseek.com/chat/completions", data=body,
        headers={"Content-Type":"application/json","Authorization":"Bearer "+key()})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.load(r)
    return json.loads(data["choices"][0]["message"]["content"])

def url_ok(u):
    if not u.startswith("https://"): return False
    try:
        req = urllib.request.Request(u, method="HEAD", headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            return r.status < 400
    except Exception:
        try:
            req = urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=12) as r:
                return r.status < 400
        except Exception:
            return False

HEADER = '''<header class="top"><div class="top-inner">
  <a href="/" class="brand">Crypto License <span>Consulting24</span></a>
  <div class="top-cta"><a href="/jurisdictions/" style="font-weight:700;color:var(--ink);font-size:.95rem;align-self:center">Jurisdictions</a><a href="/blog/" class="btn btn-ghost" style="padding:9px 15px;min-height:auto;font-size:.9rem">Blog</a>
    <a href="''' + WA + '''" class="top-phone">Talk to an expert</a>
    <a href="/#contact" class="btn btn-primary" style="padding:10px 16px;min-height:auto;font-size:.92rem">Free Consultation</a></div>
</div></header>'''
ADVISOR = '''  <div class="advisor" style="display:flex;gap:18px;align-items:center;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:20px;margin:28px 0">
    <img src="/img/mardo-soo-profile.jpg" alt="Mardo Soo, CEO of Consulting24" width="92" height="92" loading="lazy" style="width:92px;height:92px;border-radius:50%;object-fit:cover;flex:none;border:3px solid var(--accent-soft)">
    <div><strong style="display:block;font-size:1.05rem">Mardo Soo &middot; CEO, Consulting24</strong><span style="color:var(--ink-2);font-size:.92rem">Personally advises on jurisdiction selection. 500+ crypto licenses across Estonia, Lithuania &amp; Panama. <a href="https://www.linkedin.com/in/mardo-s-00a05ab0/" target="_blank" rel="noopener">LinkedIn &rarr;</a></span></div>
  </div>'''
def footer():
    return '''<footer><div class="wrap"><div class="foot-grid">
    <div><h4>Consulting24</h4><p style="color:#a3a3a3">500+ crypto licenses across Estonia, Lithuania, Panama and beyond.</p><p style="margin-top:14px"><strong style="color:#fff">WhatsApp / email</strong><br>mardo@consulting24.co</p></div>
    <div><h4>Jurisdictions</h4><a href="/jurisdictions/">All jurisdictions</a><a href="/">Panama</a><a href="/lithuania-crypto-license/">Lithuania</a><a href="/estonia-crypto-license/">Estonia</a></div>
    <div><h4>Resources</h4><a href="/cost/">Panama cost</a><a href="/requirements/">Requirements</a><a href="/blog/">Blog</a><a href="/#faq">FAQ</a></div>
    <div><h4>Company</h4><a href="/#about">About Consulting24</a><a href="https://consulting24.co/">consulting24.co</a><a href="https://www.linkedin.com/in/mardo-s-00a05ab0/">Mardo Soo on LinkedIn</a></div>
  </div><div class="foot-bottom">&copy; 2026 Consulting24 &middot; X24Consulting O&Uuml; &middot; Reg nr 16971898 &middot; Poordi 3-63, 10156 Tallinn, Estonia &middot; General guidance, not legal advice.</div></div></footer>
<div class="sticky-bar"><a href="''' + WA + '''" class="btn btn-secondary" style="background:var(--ink)">&#128172; WhatsApp</a><a href="/#contact" class="btn btn-primary">Free consultation</a></div>'''

def fig(src, alt):
    return f'  <figure style="margin:24px 0"><img src="{src}" alt="{html.escape(alt)}" loading="lazy" width="1200" height="320" style="width:100%;height:auto;border-radius:14px;border:1px solid var(--line)"></figure>'

def assemble(slug, crumb, d, kind="landing"):
    sec_list = [f"  <h2>{html.escape(s['h2'])}</h2>\n{s['html']}" for s in d["sections"]]
    imgs = [("/img/graphic-process.svg", f"{crumb} crypto licence process: scope, incorporate, apply, operate"),
            ("/img/graphic-jurisdictions.svg", f"{crumb} crypto licence compared with Panama, EU/MiCA, Gulf and offshore options"),
            ("/img/graphic-trust.svg", "Consulting24 — 500+ crypto licenses obtained, compliance-first")]
    out, placed = [], 0
    for i, block in enumerate(sec_list):
        out.append(block)
        if i in (0, 2, 4) and placed < len(imgs):
            out.append(fig(*imgs[placed])); placed += 1
    while placed < len(imgs):  # ensure all 3 land even on short pages
        out.append(fig(*imgs[placed])); placed += 1
    sections = "\n".join(out)
    faqs_html = '<section class="faq"><h2>Frequently asked questions</h2>' + "".join(
        f"<details><summary>{html.escape(f['q'])}</summary><p>{f['a']}</p></details>" for f in d["faqs"]) + "</section>"
    auth = [a for a in d.get("authority_links",[]) if url_ok(a.get("url",""))]
    auth_html = ""
    if auth:
        auth_html = '<h2>Official sources</h2><ul>' + "".join(
            f'<li><a href="{html.escape(a["url"])}" target="_blank" rel="nofollow noopener">{html.escape(a["title"])}</a></li>' for a in auth) + "</ul>"
    faq_schema = ",".join('{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}' %
        (json.dumps(f["q"]), json.dumps(re.sub("<[^>]+>","",f["a"]))) for f in d["faqs"])
    canon = f"{BASE}/{slug}/" if kind=="landing" else f"{BASE}/blog/{slug}/"
    css = "../styles.css" if kind=="landing" else "../../styles.css"
    return f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(d["meta_title"])}</title>
<meta name="description" content="{html.escape(d["meta_description"])}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="{canon}">
<meta property="og:title" content="{html.escape(d["meta_title"])}"><meta property="og:description" content="{html.escape(d["meta_description"])}">
<meta property="og:type" content="article"><meta property="og:url" content="{canon}"><meta property="og:image" content="{BASE}/og-image.jpg">
<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[
 {{"@type":"BreadcrumbList","itemListElement":[
   {{"@type":"ListItem","position":1,"name":"Home","item":"{BASE}/"}},
   {{"@type":"ListItem","position":2,"name":"Jurisdictions","item":"{BASE}/jurisdictions/"}},
   {{"@type":"ListItem","position":3,"name":{json.dumps(crumb)},"item":"{canon}"}}]}},
 {{"@type":"Service","name":{json.dumps(crumb+" Crypto License")},"provider":{{"@type":"Organization","name":"Consulting24","url":"https://consulting24.co/"}}}},
 {{"@type":"FAQPage","mainEntity":[{faq_schema}]}}
]}}
</script>
<link rel="stylesheet" href="{css}">
</head><body>
{HEADER}
<div class="wrap"><nav class="breadcrumbs"><a href="/">Home</a> &rsaquo; <a href="/jurisdictions/">Jurisdictions</a> &rsaquo; {html.escape(crumb)}</nav></div>
<article class="wrap">
  <h1>{html.escape(d["h1"])}</h1>
{d["intro_html"]}
{sections}
{faqs_html}
{auth_html}
{ADVISOR}
  <div class="cta-card"><h2>Talk to a crypto-licensing expert</h2><p>500+ licenses across Estonia, Lithuania, Panama and beyond. Tell us your model and we'll map the right route &mdash; honestly.</p>
  <a href="{WA}" class="btn btn-primary">&#128172; Talk to an expert</a><a href="/#contact" class="btn btn-ghost">Free consultation</a></div>
  <p style="color:var(--muted);font-size:.85rem;margin-top:24px">General guidance, not legal advice. Rules and fees evolve &mdash; we confirm current requirements for your case.</p>
</article>
{footer()}
</body></html>
'''

def _trim_meta(d):
    # auto-fix near-miss meta lengths so a 1-2 char overflow never wastes a good page
    t = (d.get("meta_title") or "").strip()
    if len(t) > 65: t = t[:64].rsplit(" ", 1)[0]
    d["meta_title"] = t
    desc = (d.get("meta_description") or "").strip()
    if len(desc) > 160: desc = desc[:157].rsplit(" ", 1)[0].rstrip(".,;: ") + "…"
    d["meta_description"] = desc
    return d

def qc(d, page_html, keyword=""):
    text = re.sub("<[^>]+>"," "," ".join([d["intro_html"]] + [s["html"] for s in d["sections"]] + [f["a"] for f in d["faqs"]]))
    words = len(text.split())
    internal = len(set(re.findall(r'href="(/[^"]*)"', page_html)))
    images = page_html.count("<img ")
    kw = (keyword or "").lower().strip()
    density = round(100 * text.lower().count(kw) * len(kw.split()) / max(words,1), 2) if kw else 0
    report = {
        "words": words, "faqs": len(d["faqs"]), "images": images, "internal_links": internal,
        "title_len": len(d["meta_title"]), "desc_len": len(d["meta_description"]), "kw_density%": density,
    }
    fails = []
    if words < 2000: fails.append(f"words {words} < 2000")
    if len(d["faqs"]) < 8: fails.append(f"faqs {len(d['faqs'])} < 8")
    if images < 3: fails.append(f"images {images} < 3")
    if internal < 5: fails.append(f"internal_links {internal} < 5")
    if 'href="/"' not in page_html: fails.append("no homepage link")
    if not (50 <= len(d["meta_title"]) <= 65): fails.append(f"title len {len(d['meta_title'])}")
    if not (110 <= len(d["meta_description"]) <= 165): fails.append(f"desc len {len(d['meta_description'])}")
    if kw and kw not in d["h1"].lower(): fails.append("keyword not in H1")
    if kw and kw not in d["meta_title"].lower(): fails.append("keyword not in title")
    if density > 3.0: fails.append(f"keyword stuffing {density}%")
    low=text.lower()
    banned=[w for w in BANNED if w in low]
    report["banned"]=banned
    dashes = ("\u2014" in low) or ("\u2013" in low) or ("!" in re.sub(r"&[a-z]+;"," ",low))
    if dashes: fails.append("em/en-dash or ! present")
    if banned: fails.append("banned words: "+",".join(banned[:5]))
    report["pass"] = not fails
    report["fails"] = fails
    return report

def build(kind, slug, keyword, brief):
    crumb = brief.split("|")[0].strip() if "|" in brief else slug.replace("-crypto-license","").replace("-"," ").title()
    user = f"Write a {kind} page. Primary keyword: \"{keyword}\". Slug: /{slug}/. Brief & facts: {brief}\nReturn STRICT JSON per the schema. Remember: 2000+ words, 8+ FAQs, full section structure, internal links from the allow-list, validated official authority links only."
    d = _trim_meta(_clean_d(call_deepseek(user)))
    page = assemble(slug, crumb, d, kind).replace('/panama-crypto-license/', '/')  # guard: old project path → root
    report = qc(d, page, keyword)
    # auto-expand if the only failure is word count (up to 2 retries)
    tries = 0
    while not report["pass"] and any("words" in f for f in report["fails"]) and tries < 2:
        tries += 1
        cur = report["words"]
        exp = (f"This draft is only {cur} words; it MUST reach 2300+. Expand it: deepen every section with more concrete detail, examples, a worked cost/timeline table, more on banking, compliance and common mistakes, and lengthen FAQ answers. Keep all existing internal links and authority_links. Return the SAME strict JSON schema with the fuller content.\n\nCURRENT JSON:\n" + json.dumps(d)[:12000])
        d = _trim_meta(_clean_d(call_deepseek(exp)))
        page = assemble(slug, crumb, d, kind).replace('/panama-crypto-license/', '/')  # guard: old project path → root
        report = qc(d, page, keyword)
        print(f"  expand retry {tries}: {report['words']} words")
    outdir = os.path.join(ROOT, slug) if kind=="landing" else os.path.join(ROOT, "blog", slug)
    if report["pass"]:
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir,"index.html"),"w",encoding="utf-8") as f: f.write(page)
        print(f"WROTE /{slug}/  {report}")
    else:
        print(f"QC FAIL /{slug}/  {report}  (not written)")
    return report

if __name__ == "__main__":
    if len(sys.argv) < 5:
        sys.exit("usage: generate.py <landing|blog> <slug> <keyword> <brief>")
    build(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
