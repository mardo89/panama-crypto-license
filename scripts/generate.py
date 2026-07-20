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
import os, sys, re, json, html, urllib.request, urllib.error, hashlib, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.consulting24.co"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
try:
    from regulators import sources_block as _sources_block
except Exception:
    def _sources_block(slug): return ""
WA = "https://wa.me/37258155779?text=Hi%2C%20I%27d%20like%20to%20ask%20about%20a%20crypto%20company%20setup."

def key():
    k = os.environ.get("DEEPSEEK_API_KEY")
    if k: return k.strip()
    p = os.path.join(ROOT, "scripts", ".deepseek_key")
    if os.path.exists(p): return open(p).read().strip()
    sys.exit("No DeepSeek key (set DEEPSEEK_API_KEY or scripts/.deepseek_key)")

# Known internal URLs the model may link to (prevents broken internal links)
INTERNAL = ["/", "/cost/", "/requirements/", "/application-process/", "/exchange-license/",
  "/best-country-for-crypto-license/",
  "/company-setup/", "/vs-lithuania/", "/jurisdictions/", "/blog/",
  "/lithuania-crypto-license/", "/estonia-crypto-license/", "/dubai-crypto-license/",
  "/el-salvador-crypto-license/", "/czech-republic-crypto-license/", "/poland-crypto-license/",
  "/malta-crypto-license/", "/switzerland-crypto-license/", "/cyprus-crypto-license/",
  "/cayman-islands-crypto-license/"]

SYSTEM = """You are a senior crypto-licensing copywriter for Consulting24 (X24Consulting OU, Tallinn, Estonia), a firm that has obtained 500+ crypto licenses, delivering directly in Estonia, Lithuania and Panama and advising/coordinating in all other jurisdictions. Panama company price is a flat EUR 6,000. Write in clear, confident, expert British/EU English for crypto founders.

Output STRICT JSON only, matching this schema:
{
 "meta_title": "50-60 chars, includes the primary keyword",
 "meta_description": "120-155 chars, human, value proposition/CTA, primary keyword; MUST end with a complete sentence and a full stop, never a trailing ellipsis",
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

BANNED_MAP = {"seamless":"smooth","robust":"strong","leverage":"use","delve into":"examine","delve":"examine",
  "cutting-edge":"advanced","groundbreaking":"notable","game-changing":"significant","harness":"use",
  "unleash":"release","empower":"enable","holistic":"complete","synergy":"alignment","paradigm":"model",
  "it's worth noting that":"note that","that being said,":"still,","in essence,":"","in conclusion,":"",
  "when it comes to":"for","in today's world":"today","at the end of the day,":"ultimately,","look no further":"start here"}

def _clean(s):
    if not isinstance(s, str): return s
    for a, b in (("—", "-"), ("–", "-"), ("&mdash;", "-"), ("&ndash;", "-"), ("!", ".")):
        s = s.replace(a, b)
    for bad, good in BANNED_MAP.items():
        s = re.sub(re.escape(bad), good, s, flags=re.I)
    return re.sub(r"  +", " ", s)

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
    <div><h4>Resources</h4><a href="/cost/">Panama cost</a><a href="/best-country-for-crypto-license/">Best country for a crypto license</a><a href="/requirements/">Requirements</a><a href="/blog/">Blog</a></div>
    <div><h4>Company</h4><a href="/#about">About Consulting24</a><a href="https://consulting24.co/">consulting24.co</a><a href="https://www.linkedin.com/in/mardo-s-00a05ab0/">Mardo Soo on LinkedIn</a></div>
  </div><div class="foot-bottom">&copy; 2026 Consulting24 &middot; X24Consulting O&Uuml; &middot; Reg nr 16971898 &middot; Poordi 3-63, 10156 Tallinn, Estonia &middot; General guidance, not legal advice.</div></div></footer>
<div class="sticky-bar"><a href="''' + WA + '''" class="btn btn-secondary" style="background:var(--ink)">&#128172; WhatsApp</a><a href="/#contact" class="btn btn-primary">Free consultation</a></div>'''

def fig(src, alt):
    return f'  <figure style="margin:24px 0"><img src="{src}" alt="{html.escape(alt)}" loading="lazy" width="1200" height="320" style="width:100%;height:auto;border-radius:14px;border:1px solid var(--line)"></figure>'

_HUB_SPECIAL = {"mica":"MiCA","vasp":"VASP","casp":"CASP","msb":"MSB","vara":"VARA","bvi":"BVI",
 "usa":"USA","uae":"UAE","eu":"EU","el":"El","vs":"vs","and":"and","for":"for","of":"of",
 "hong":"Hong","kong":"Kong","south":"South","korea":"Korea","costa":"Costa","rica":"Rica",
 "saudi":"Saudi","arabia":"Arabia","czech":"Czech","republic":"Republic","marshall":"Marshall",
 "islands":"Islands","cayman":"Cayman","saint":"Saint","lucia":"Lucia","abu":"Abu","dhabi":"Dhabi"}
def _hub_label(slug):
    return " ".join(_HUB_SPECIAL.get(w.lower(), w.capitalize()) for w in slug.split("-"))
_CORE_LINKS = ["", "jurisdictions", "cost", "requirements", "mica-license",
               "casp-license", "lithuania-crypto-license", "estonia-crypto-license"]
def link_hub(self_slug="", cap=20):
    """Lean, contextual internal-link block (~20 relevant links, not the whole site).
    Picks: core money pages + same-jurisdiction/topic siblings + a deterministic slice."""
    skip = {"blog","scripts","config","img","logs","jurisdictions"}
    dirs = [n for n in sorted(os.listdir(ROOT))
            if n not in skip and os.path.isdir(os.path.join(ROOT, n))
            and os.path.exists(os.path.join(ROOT, n, "index.html"))]
    dset = set(dirs)
    picked, seen = [], {self_slug}
    def add(s):
        if s in seen: return
        if s == "" or s in dset:
            seen.add(s); picked.append(s)
    for c in _CORE_LINKS: add(c)                                  # core money pages
    toks = [t for t in self_slug.split("-") if len(t) > 3 and t != "crypto" and t != "license"]
    for s in dirs:                                                # topical siblings
        if len(picked) >= cap: break
        if any(t in s for t in toks): add(s)
    h = int(hashlib.md5(self_slug.encode()).hexdigest(), 16) if self_slug else 0
    rotated = dirs[h % len(dirs):] + dirs[:h % len(dirs)] if dirs else []
    for s in rotated:                                            # fill remainder, varied per page
        if len(picked) >= cap: break
        add(s)
    links = "".join(
        f'<a href="/{s}/" style="display:inline-block;margin:0 10px 8px 0">{_hub_label(s) if s else "Panama (EUR 6,000)"}</a>'
        for s in picked[:cap])
    if not links: return ""
    return ('<section class="wrap landing-link-hub" style="margin:8px auto 0">'
            '<h2 style="font-size:1.3rem">Related crypto license guides</h2>'
            '<p style="color:var(--ink-2)">Compare the most relevant routes, each with cost, capital, timeline and requirements:</p>'
            f'<div style="line-height:1.9;font-size:14px">{links}</div></section>')

_BLOG_STOP = {"crypto","license","licence","company","which","choose","should","your","panama",
              "for","the","and","vs","cost","take","2026","how","get","guide","in","to","of","a"}
def _blog_related(self_slug):
    """Blog footer: link the #2-ranking best-country money page + 2-3 topically related
    blog posts (token overlap) so posts form clusters instead of sitting siloed."""
    bdir = os.path.join(ROOT, "blog")
    try:
        cand = [n for n in os.listdir(bdir)
                if n != self_slug and os.path.isdir(os.path.join(bdir, n))
                and os.path.exists(os.path.join(bdir, n, "index.html"))]
    except FileNotFoundError:
        cand = []
    toks = {t for t in self_slug.split("-") if len(t) > 3 and t not in _BLOG_STOP}
    scored = sorted(cand, key=lambda s: -len(toks & set(s.split("-"))))
    rel = [s for s in scored if toks & set(s.split("-"))][:3] or scored[:3]
    posts = "".join(f'<a href="/blog/{s}/"><strong>{_hub_label(s)}</strong></a>' for s in rel)
    return ('<h2>Related guides</h2><div class="related">'
            '<a href="/best-country-for-crypto-license/"><strong>Best country for a crypto license</strong>'
            '<span>Compare every jurisdiction</span></a>' + posts + '</div>')

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
    _pool = [("/lithuania-crypto-license/","Lithuania"),("/estonia-crypto-license/","Estonia"),("/dubai-crypto-license/","Dubai"),("/cyprus-crypto-license/","Cyprus"),("/malta-crypto-license/","Malta"),("/cayman-islands-crypto-license/","Cayman Islands"),("/switzerland-crypto-license/","Switzerland"),("/","Panama (EUR 6,000)")]
    _rel = [(h,n) for h,n in _pool if h.strip("/") != slug][:4]
    def _rel_anchor(h, n):
        label = n if "(" in n else f"{n} crypto license"   # descriptive partial-match anchor
        return f'<a href="{h}"><strong>{label}</strong><span>Requirements, cost &amp; timeline</span></a>'
    related_html = '<h2>Related jurisdictions</h2><div class="related">' + "".join(_rel_anchor(h, n) for h, n in _rel) + '</div>'
    blog_extra = '' if kind == "landing" else _blog_related(slug)
    topcta = '<div class="top-cta-row"><a href="'+WA+'" class="btn btn-primary">&#128172; Talk to an expert</a><a href="/#contact" class="btn btn-ghost">Free assessment</a></div>'
    trust = '<div class="trust-strip"><b>500+ crypto licenses obtained.</b> <span class="logos">Binance &middot; LBank &middot; Coinify &middot; MultiversX &middot; UPay &middot; Vitalum</span></div>'
    today = datetime.date.today().isoformat()
    # TL;DR answer box (LLM + featured-snippet friendly: a direct, quotable answer up top)
    _ans = html.escape(d.get("meta_description","").strip())
    tldr = (f'<div class="answer-box" style="background:var(--accent-soft);border-left:4px solid var(--accent);'
            f'border-radius:8px;padding:16px 20px;margin:0 0 22px"><strong style="color:var(--accent-dark)">Short answer:</strong> {_ans}</div>') if _ans else ""
    # Visible author byline (E-E-A-T)
    byline = (f'<p class="byline" style="color:var(--muted);font-size:.9rem;margin:0 0 18px">'
              f'By <a href="https://www.linkedin.com/in/mardo-s-00a05ab0/" rel="author">Mardo Soo</a>, '
              f'Founder &amp; CEO, Consulting24 (X24Consulting O&Uuml;) &middot; Updated {today}</p>')
    _authorimg = f"{BASE}/img/mardo-soo-profile.jpg"
    article_schema = (
      f'{{"@type":"Article","headline":{json.dumps(d.get("meta_title",""))},'
      f'"description":{json.dumps(d.get("meta_description",""))},'
      f'"datePublished":"{today}","dateModified":"{today}",'
      f'"image":"{BASE}/og-image.jpg","mainEntityOfPage":"{canon}",'
      f'"author":{{"@type":"Person","name":"Mardo Soo","jobTitle":"Founder & CEO",'
      f'"url":"https://www.linkedin.com/in/mardo-s-00a05ab0/","image":"{_authorimg}",'
      f'"worksFor":{{"@type":"Organization","name":"Consulting24","url":"https://consulting24.co/"}}}},'
      f'"publisher":{{"@type":"Organization","name":"Consulting24","url":"https://consulting24.co/",'
      f'"logo":{{"@type":"ImageObject","url":"{BASE}/img/mardo-soo-profile.jpg"}}}}}}')
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
 {article_schema},
 {{"@type":"FAQPage","mainEntity":[{faq_schema}]}}
]}}
</script>
<link rel="stylesheet" href="{css}">
</head><body>
{HEADER}
<div class="wrap"><nav class="breadcrumbs"><a href="/">Home</a> &rsaquo; <a href="/jurisdictions/">Jurisdictions</a> &rsaquo; {html.escape(crumb)}</nav></div>
<article class="wrap">
  <h1>{html.escape(d["h1"])}</h1>
{byline}
{tldr}
{d["intro_html"]}
{topcta}
{trust}
{sections}
{faqs_html}
{auth_html}
{_sources_block(slug)}
{related_html}
{ADVISOR}
  <div class="cta-card"><h2>Talk to a crypto-licensing expert</h2><p>500+ licenses across Estonia, Lithuania, Panama and beyond. Tell us your model and we'll map the right route &mdash; honestly.</p>
  <a href="{WA}" class="btn btn-primary">&#128172; Talk to an expert</a><a href="/#contact" class="btn btn-ghost">Free consultation</a></div>
  <p style="color:var(--muted);font-size:.85rem;margin-top:24px">General guidance, not legal advice. Rules and fees evolve &mdash; we confirm current requirements for your case.</p>
</article>
{link_hub(slug) if kind=="landing" else blog_extra}
{footer()}
</body></html>
'''

def tidy_desc(s):
    """Trim a meta description to a COMPLETE sentence <=155 chars, never a mid-word
    cut with a trailing ellipsis (the pre-2026-07 bug left 380 pages ending in '…')."""
    s = re.sub(r"\s*(?:\.{2,}|…)+\s*$", "", (s or "").strip()).strip()
    if len(s) <= 158 and s[-1:] in ".!?":
        return s
    cut = s[:156].rstrip()
    ends = [m.end() - 1 for m in re.finditer(r"[.!?]", cut)]
    if ends and ends[-1] >= 90:                       # keep to last full sentence
        return cut[:ends[-1] + 1].strip()
    commas = [i for i, c in enumerate(cut) if c == "," and i >= 60]
    base = cut[:commas[-1]] if commas else cut.rsplit(" ", 1)[0]   # drop trailing incomplete clause
    return base.rstrip(" ,;:-") + "."

def _trim_meta(d):
    # auto-fix near-miss meta lengths so overflow never wastes a good page
    t = (d.get("meta_title") or "").strip()
    if len(t) > 60: t = t[:60].rsplit(" ", 1)[0].rstrip(" -|:&")   # <=~600px, no dangling punct
    d["meta_title"] = t
    d["meta_description"] = tidy_desc(d.get("meta_description") or "")
    return d

def _repair(d, keyword):
    """Auto-fix the deterministic QC failures (keyword-in-H1/title, title length)
    so quality pages are never dropped for a mechanical SEO miss. Keyword is always
    prepended to the front, so any right-side trim preserves it."""
    kw = (keyword or "").strip()
    if not kw:
        return d
    kwl = kw.lower()
    _keep = {"and","for","of","to","the","vs","a","in"}
    kwt = " ".join(_HUB_SPECIAL.get(w.lower(), w if w.isupper() else (w.lower() if w.lower() in _keep else w.capitalize()))
                   for w in kw.split())
    if kwt[:1].islower():
        kwt = kwt[:1].upper() + kwt[1:]
    # Keyword is "present" if every keyword token already appears as a whole word,
    # even reordered (e.g. kw "crypto staking license portugal" vs title
    # "Portugal Crypto License: Crypto Staking"). This prevents re-prepending the
    # keyword onto a title that already covers it, which produced duplicated junk
    # like "Crypto Staking License Portugal Crypto License: Crypto Staking".
    def _covers(text):
        low = text.lower()
        return all(re.search(r'\b' + re.escape(tok) + r'\b', low) for tok in kwl.split())
    # H1 must contain the keyword
    h1 = (d.get("h1") or "").strip()
    if not _covers(h1):
        d["h1"] = f"{kwt}: {h1}" if h1 else f"{kwt}: 2026 Guide"
    # Title must contain the keyword
    t = (d.get("meta_title") or "").strip()
    if not _covers(t):
        t = f"{kwt}: {t}".strip() if t else kwt
    # Title must be 50-65 chars
    if len(t) < 50:
        base = t.rstrip(" .:")
        # avoid a double year / double colon when the title already reads cleanly
        t = (base + " — Cost, Requirements & Timeline") if "2026" in base \
            else (base + " 2026: Cost, Requirements & Timeline")
    if len(t) > 65:
        t = t[:65].rsplit(" ", 1)[0].rstrip(" .,:;&-—")
    d["meta_title"] = t
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
    # token-coverage (reordered keyword counts as present), matching _repair
    _toks = lambda s: all(re.search(r'\b'+re.escape(t)+r'\b', s.lower()) for t in kw.split())
    if kw and not _toks(d["h1"]): fails.append("keyword not in H1")
    if kw and not _toks(d["meta_title"]): fails.append("keyword not in title")
    if density > 3.0: fails.append(f"keyword stuffing {density}%")
    low=text.lower()
    banned=[w for w in BANNED if w in low]
    report["banned"]=banned
    dashes = ("\u2014" in low) or ("\u2013" in low) or ("!" in re.sub(r"&[a-z]+;"," ",low))
    if dashes: fails.append("em/en-dash or ! present")
    # banned words are auto-replaced in _clean; report only, don't hard-fail
    report["pass"] = not fails
    report["fails"] = fails
    return report

def build(kind, slug, keyword, brief):
    crumb = brief.split("|")[0].strip() if "|" in brief else slug.replace("-crypto-license","").replace("-"," ").title()
    user = f"Write a {kind} page. Primary keyword: \"{keyword}\". Slug: /{slug}/. Brief & facts: {brief}\nReturn STRICT JSON per the schema. Remember: 2000+ words, 8+ FAQs, full section structure, internal links from the allow-list, validated official authority links only."
    d = _repair(_trim_meta(_clean_d(call_deepseek(user))), keyword)
    page = assemble(slug, crumb, d, kind).replace('/panama-crypto-license/', '/').replace('/panama/', '/')  # guard: old project path → root
    report = qc(d, page, keyword)
    # auto-expand if the only failure is word count (up to 2 retries)
    tries = 0
    while not report["pass"] and any("words" in f for f in report["fails"]) and tries < 2:
        tries += 1
        cur = report["words"]
        exp = (f"This draft is only {cur} words; it MUST reach 2300+. Expand it: deepen every section with more concrete detail, examples, a worked cost/timeline table, more on banking, compliance and common mistakes, and lengthen FAQ answers. Keep all existing internal links and authority_links. Return the SAME strict JSON schema with the fuller content.\n\nCURRENT JSON:\n" + json.dumps(d)[:12000])
        d = _repair(_trim_meta(_clean_d(call_deepseek(exp))), keyword)
        page = assemble(slug, crumb, d, kind).replace('/panama-crypto-license/', '/').replace('/panama/', '/')  # guard: old project path → root
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
