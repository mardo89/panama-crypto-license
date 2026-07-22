#!/usr/bin/env python3
"""news_auto.py — automated news desk, sourced-only.

Polls real regulator feeds, and for anything new and crypto-relevant it fetches the
actual document, summarises ONLY that document, and publishes through news.py's gates.
On a day when no regulator publishes anything relevant, it publishes nothing. That is
the intended behaviour, not a failure.

Why it is built this way: this site has already published four invented laws and two
invented regulators, all produced by asking an LLM to write about a topic from memory.
So the model here is never asked what it knows. It is handed a document that was just
downloaded and asked to report only what is in it, and then:

  1. GROUNDING GATE - every number, acronym and proper noun in the generated text must
     appear in the source document, or the item is rejected outright.
  2. The "What this means" operator paragraph is NOT model-written. It comes from a
     fixed template keyed on jurisdiction, so 100% of model output faces the gate with
     no exempt sections.
  3. news.publish() then re-applies its own checks: source URL must resolve, fabrication
     markers refused, length and headline limits.

Anything that fails is logged to logs/news_auto.log and skipped. Under-publishing is the
correct failure mode.

    news_auto.py --dry-run     poll and show what it would publish, write nothing
    news_auto.py               poll and publish (default cap 2 items per run)
    news_auto.py --max 1       tighter cap
    news_auto.py --feeds       just check every feed is still alive
"""
from __future__ import annotations
import argparse
import datetime as dt
import html as htmllib
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import news  # the manual desk: rendering, gates, store  # noqa: E402

ROOT = news.ROOT
SEEN = os.path.join(ROOT, "config", "news_seen.json")
LOG = os.path.join(ROOT, "logs", "news_auto.log")
UA = {"User-Agent": "Mozilla/5.0 (compatible; Consulting24NewsDesk/1.0)"}

MAX_PER_RUN = 2          # a lead-gen site posting 10 regulator summaries a day looks like spam
MAX_AGE_DAYS = 14        # older than this is not news any more
MIN_SOURCE_CHARS = 1200  # below this the source is a stub, not enough to report from
ATOM = "{http://www.w3.org/2005/Atom}"

# Only feeds verified to return a parseable feed. Re-check with --feeds; regulators move
# these URLs without notice, and a silently dead feed is how a news desk quietly stops.
FEEDS = [
    {"key": "esma", "name": "ESMA", "jurisdiction": "European Union",
     "publisher": "European Securities and Markets Authority (ESMA)",
     "url": "https://www.esma.europa.eu/rss.xml"},
    {"key": "eba", "name": "EBA", "jurisdiction": "European Union",
     "publisher": "European Banking Authority (EBA)",
     "url": "https://www.eba.europa.eu/rss.xml"},
    {"key": "mfsa", "name": "MFSA", "jurisdiction": "Malta",
     "publisher": "Malta Financial Services Authority (MFSA)",
     "url": "https://www.mfsa.mt/feed/"},
    {"key": "fca", "name": "FCA", "jurisdiction": "United Kingdom",
     "publisher": "Financial Conduct Authority (FCA)",
     "url": "https://www.fca.org.uk/news/rss.xml"},
    {"key": "sec", "name": "SEC", "jurisdiction": "United States",
     "publisher": "U.S. Securities and Exchange Commission (SEC)",
     "url": "https://www.sec.gov/news/pressreleases.rss", "dmy": False},
]

# These feeds are mostly not about crypto. Everything else is dropped before it costs a fetch.
RELEVANT = re.compile(
    r"crypto|mica\b|casp\b|vasp\b|virtual asset|digital asset|stablecoin|"
    r"e-money token|asset-referenced|tokenis|tokeniz|distributed ledger|\bdlt\b|"
    r"bitcoin|blockchain", re.I)

# The operator read is templated, never model-written, so no model sentence escapes the gate.
OPERATOR_LINE = {
    "European Union": (
        "What this means: EU rules set the floor for anyone serving EU clients, so a change here "
        "usually changes the sequencing of an application rather than the destination. Consulting24 "
        "delivers CASP-track company and licensing work directly in Estonia and Lithuania, and the "
        "binding constraint is normally the regulator's queue rather than the incorporation."),
    "Malta": (
        "What this means: Malta is a MiCA jurisdiction, so an MFSA move is worth reading against the "
        "same requirements applying in Estonia and Lithuania, where Consulting24 delivers directly. "
        "We advise and coordinate on Malta rather than filing there ourselves."),
    "United Kingdom": (
        "What this means: the UK sits outside MiCA, so a UK change does not carry across to an EU "
        "authorisation and vice versa. If you need both markets, they are two separate projects with "
        "separate timelines, and we would rather say so up front than sell one as covering the other."),
    "United States": (
        "What this means: US rules apply to US market access and do not substitute for an EU "
        "authorisation. Consulting24 does not file with the SEC. We flag developments here because "
        "they change where founders choose to serve clients from, not because we advise on them."),
}
DEFAULT_OPERATOR = (
    "What this means: rules in one jurisdiction rarely transfer to another, so treat this as input to "
    "where you licence rather than a change to an application already under way. Consulting24 delivers "
    "directly in Estonia, Lithuania and Panama, and advises on the rest.")


def log(msg: str) -> None:
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    line = f"{dt.datetime.now().isoformat(timespec='seconds')} {msg}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


def _load_seen() -> dict:
    if os.path.exists(SEEN):
        with open(SEEN, encoding="utf-8") as f:
            return json.load(f)
    return {"seen": {}}


def _save_seen(state: dict) -> None:
    os.makedirs(os.path.dirname(SEEN), exist_ok=True)
    with open(SEEN, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, ensure_ascii=False)
        f.write("\n")


def _get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# ---------------------------------------------------------------- feed polling

def _parse_date(text: str):
    text = (text or "").strip()
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            d = dt.datetime.strptime(text, fmt)
            return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
    try:  # ISO with fractional seconds etc.
        d = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def poll_feed(feed: dict) -> list:
    try:
        root = ET.fromstring(_get(feed["url"]))
    except Exception as exc:  # noqa: BLE001
        log(f"FEED-DEAD {feed['key']}: {type(exc).__name__}: {exc}")
        return []
    out = []
    for el in root.findall(".//item"):
        out.append({"title": (el.findtext("title") or "").strip(),
                    "link": (el.findtext("link") or "").strip(),
                    "summary": (el.findtext("description") or "").strip(),
                    "date": _parse_date(el.findtext("pubDate") or "")})
    for el in root.findall(f".//{ATOM}entry"):
        link_el = el.find(f"{ATOM}link")
        out.append({"title": (el.findtext(f"{ATOM}title") or "").strip(),
                    "link": (link_el.get("href") if link_el is not None else "") or "",
                    "summary": (el.findtext(f"{ATOM}summary") or "").strip(),
                    "date": _parse_date(el.findtext(f"{ATOM}updated")
                                        or el.findtext(f"{ATOM}published") or "")})
    for e in out:
        e["feed"] = feed
    return out


def candidates(max_age_days: int) -> list:
    seen = _load_seen()["seen"]
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=max_age_days)
    found = []
    for feed in FEEDS:
        for e in poll_feed(feed):
            if not e["link"] or not e["title"]:
                continue
            if e["link"] in seen:
                continue
            if e["date"] and e["date"] < cutoff:
                continue
            if not RELEVANT.search(e["title"] + " " + e["summary"]):
                continue
            found.append(e)
    found.sort(key=lambda e: e["date"] or dt.datetime.min.replace(tzinfo=dt.timezone.utc),
               reverse=True)
    return found


# ---------------------------------------------------------------- source text

def _html_to_text(raw: bytes) -> str:
    s = raw.decode("utf-8", "ignore")
    s = re.sub(r"(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s)).strip()


def _pdf_to_text(raw: bytes) -> str:
    import io
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError:
            return ""
    try:
        reader = PdfReader(io.BytesIO(raw))
        return re.sub(r"\s+", " ", " ".join(p.extract_text() or "" for p in reader.pages))
    except Exception:  # noqa: BLE001
        return ""


_MONTHS = ("January February March April May June July August September October "
           "November December").split()


def sniff_source_date(text: str, dmy: bool = True):
    """Several regulator feeds (ESMA's among them) carry no date element at all, so take
    the document's own date when it states one near the top. Returns YYYY-MM-DD or ''.

    A bare numeric date is ambiguous (08/07 is 8 July in Brussels and 7 August in
    Washington), so the day/month order comes from the feed's own convention rather than
    a guess. If it still cannot be resolved, return nothing: a blank date is honest, a
    wrong one is not.
    """
    head = text[:2500]
    m = re.search(r"\b(\d{1,2})\s+(" + "|".join(_MONTHS) + r")\s+(20\d{2})\b", head)
    if m:
        return f"{m.group(3)}-{_MONTHS.index(m.group(2)) + 1:02d}-{int(m.group(1)):02d}"
    m = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", head)
    if m:
        return m.group(0)
    m = re.search(r"\b(\d{2})/(\d{2})/(20\d{2})\b", head)
    if m:
        a, b, year = int(m.group(1)), int(m.group(2)), m.group(3)
        day, month = (a, b) if dmy else (b, a)
        if 1 <= day <= 31 and 1 <= month <= 12:
            return f"{year}-{month:02d}-{day:02d}"
    return ""


def fetch_source(url: str) -> str:
    try:
        raw = _get(url, timeout=45)
    except Exception as exc:  # noqa: BLE001
        log(f"SOURCE-FETCH-FAIL {url}: {type(exc).__name__}: {exc}")
        return ""
    if raw[:5] == b"%PDF-" or url.lower().endswith(".pdf"):
        return _pdf_to_text(raw)
    return _html_to_text(raw)


# ---------------------------------------------------------------- the model call

PROMPT = """You are a financial-regulation reporter. Below is the full text of a document \
published by {publisher}. Write a short news report about it.

ABSOLUTE RULES:
- Use ONLY facts contained in the document text below. You have no other knowledge.
- Do not add background, context, history, comparisons, or implications from memory.
- Do not name any law, regulation, article number, authority, date, amount or deadline \
that does not appear verbatim in the document text.
- If the document does not say something, do not say it.
- No em dashes, no exclamation marks. Plain UK English.

Return STRICT JSON with exactly these keys:
  "headline": under 100 characters, factual, no hype, reflects the document
  "summary":  a standfirst of 60 to 280 characters
  "body":     500 to 750 words of reporting. Open with a paragraph, NOT a heading, and do \
not repeat the headline anywhere. Use "## Subheading" lines further down to break it up. \
Report what the document says and attribute statements to {publisher}. Do not carry over \
website furniture such as navigation labels, cookie notices or "Publication Details".

DOCUMENT TITLE: {title}

DOCUMENT TEXT:
{text}
"""


def ask_model(publisher: str, title: str, text: str):
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        p = os.path.join(ROOT, "scripts", ".deepseek_key")
        if os.path.exists(p):
            key = open(p, encoding="utf-8").read().strip()
    if not key:
        log("NO-KEY: set DEEPSEEK_API_KEY or scripts/.deepseek_key")
        return None
    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": PROMPT.format(
            publisher=publisher, title=title, text=text[:28000])}],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }).encode()
    req = urllib.request.Request("https://api.deepseek.com/chat/completions", data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            payload = json.loads(r.read())
        return json.loads(payload["choices"][0]["message"]["content"])
    except Exception as exc:  # noqa: BLE001
        log(f"MODEL-FAIL: {type(exc).__name__}: {exc}")
        return None


# ---------------------------------------------------------------- grounding gate

STOPWORDS = {
    "The", "This", "That", "These", "Those", "It", "In", "On", "At", "For", "By", "With",
    "From", "To", "And", "But", "As", "If", "When", "Where", "While", "After", "Before",
    "Under", "Over", "A", "An", "Its", "Their", "There", "Firms", "Clients", "However",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "January", "February", "March", "April", "May", "June", "July", "August",
    "September", "October", "November", "December",
}


def _norm(s: str) -> str:
    """Fold the things that differ cosmetically between a PDF and a rewrite."""
    s = s.lower().replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("—", " ").replace("–", "-").replace(" ", " ")
    s = re.sub(r"[,  ]", "", s)          # thousands separators
    return re.sub(r"\s+", " ", s)


# Capitalised sequences, matched with a literal space so a match never spans a line break
# (that produced phantom phrases like "Publication Date\n\nThe" and false rejections).
_NAME_RE = re.compile(r"\b[A-Z][a-z]{2,}(?:[ ][A-Z][a-z]{2,}){0,4}\b")


def grounding_report(generated: str, source: str) -> list:
    """Return the checkable tokens in `generated` that do NOT appear in `source`.

    Three classes of token carry factual weight and are checked: numbers, acronyms, and
    multi-word proper nouns. A lone capitalised word is not checked when it opens a
    sentence or a heading, because that is ordinary English capitalisation ("Additionally",
    "Scope") rather than a claim, and flagging it drowns the real signal in noise.
    """
    src = _norm(source)
    ungrounded = []

    for num in set(re.findall(r"\d[\d.]*%?", generated)):
        num = num.rstrip(".")                 # a sentence-final full stop is not part of the number
        if not num or (len(num) < 2 and num.isdigit()):
            continue                          # bare single digits are noise
        if _norm(num) not in src:
            ungrounded.append(f"number {num!r}")

    for acr in set(re.findall(r"\b[A-Z]{2,6}\b", generated)):
        if acr in {"UK", "US", "EU"}:
            continue
        if _norm(acr) not in src:
            ungrounded.append(f"acronym {acr!r}")

    # walk sentence by sentence so "first word of a sentence" is knowable
    for sentence in re.split(r"(?<=[.:;?])\s+|\n+", generated):
        s = sentence.strip().lstrip("#").strip()
        if not s:
            continue
        for m in _NAME_RE.finditer(s):
            parts = m.group(0).split()
            if m.start() == 0 and len(parts) == 1:
                continue                      # sentence/heading opener, ordinary English
            # strip a leading article ("The Panama Financial Innovation Board") rather than
            # discarding the whole phrase, which is how a fabricated entity used to slip past
            while parts and parts[0] in STOPWORDS:
                parts.pop(0)
            if not parts or (len(parts) == 1 and parts[0] in STOPWORDS):
                continue
            name = " ".join(parts)
            if _norm(name) not in src:
                ungrounded.append(f"name {name!r}")

    return sorted(set(ungrounded))


# ---------------------------------------------------------------- publishing

def build_draft(entry: dict, art: dict, operator: str, source_text: str = "") -> str:
    f = entry["feed"]
    kws = ["crypto licence", "regulation", f["name"]]
    if re.search(r"mica|casp", art["headline"] + art["body"], re.I):
        kws += ["MiCA", "CASP"]
    body = art["body"].rstrip() + "\n\n" + operator + "\n"
    sdate = (entry["date"].date().isoformat() if entry["date"]
             else sniff_source_date(source_text, f.get("dmy", True)))
    return (f"title: {art['headline']}\n"
            f"summary: {art['summary']}\n"
            f"source_name: {f['publisher']}\n"
            f"source_url: {entry['link']}\n"
            f"source_date: {sdate}\n"
            f"jurisdiction: {f['jurisdiction']}\n"
            f"keywords: {', '.join(kws)}\n\n"
            f"{body}")


def process(entry: dict, dry: bool) -> bool:
    title = entry["title"][:90]
    log(f"CANDIDATE [{entry['feed']['key']}] {title}")

    text = fetch_source(entry["link"])
    if len(text) < MIN_SOURCE_CHARS:
        log(f"  SKIP: source text only {len(text)} chars (need {MIN_SOURCE_CHARS})")
        return False

    art = ask_model(entry["feed"]["publisher"], entry["title"], text)
    if not art or not all(k in art for k in ("headline", "summary", "body")):
        log("  SKIP: model returned nothing usable")
        return False

    ungrounded = grounding_report(art["headline"] + "\n" + art["summary"] + "\n" + art["body"], text)
    if ungrounded:
        log(f"  REJECTED by grounding gate ({len(ungrounded)}): {'; '.join(ungrounded[:8])}")
        return False
    log("  grounding gate passed")

    operator = OPERATOR_LINE.get(entry["feed"]["jurisdiction"], DEFAULT_OPERATOR)
    draft = build_draft(entry, art, operator, text)
    slug = news.slugify(art["headline"])

    if dry:
        log(f"  DRY-RUN would publish /news/{slug}/")
        print("\n" + draft[:1400] + "\n" + "-" * 70)
        return True

    os.makedirs(news.DRAFTS, exist_ok=True)
    path = os.path.join(news.DRAFTS, f"{slug}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(draft)
    try:
        news.cmd_publish(slug)          # re-applies source-resolves + fabrication-marker gates
    except SystemExit as exc:
        log(f"  REFUSED by news.publish: {exc}")
        return False
    log(f"  PUBLISHED /news/{slug}/")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max", type=int, default=MAX_PER_RUN)
    ap.add_argument("--max-age-days", type=int, default=MAX_AGE_DAYS)
    ap.add_argument("--feeds", action="store_true", help="health-check the feeds and exit")
    args = ap.parse_args()

    if args.feeds:
        for f in FEEDS:
            items = poll_feed(f)
            rel = [e for e in items if RELEVANT.search(e["title"] + " " + e["summary"])]
            print(f"{f['key']:6} items={len(items):3} crypto-relevant={len(rel):2}  {f['url']}")
        return

    cands = candidates(args.max_age_days)
    log(f"RUN: {len(cands)} new crypto-relevant entries across {len(FEEDS)} feeds")
    if not cands:
        log("nothing to publish today, which is a normal outcome")
        return

    state = _load_seen()
    published = 0
    for entry in cands:
        if published >= args.max:
            break
        ok = process(entry, args.dry_run)
        if not args.dry_run:
            # mark seen either way, so a rejected item is not retried forever
            state["seen"][entry["link"]] = {
                "date": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "feed": entry["feed"]["key"], "title": entry["title"][:120],
                "published": bool(ok)}
            _save_seen(state)
        if ok:
            published += 1
    log(f"DONE: published {published} item(s)")


if __name__ == "__main__":
    main()
