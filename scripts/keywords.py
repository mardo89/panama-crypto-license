#!/usr/bin/env python3
"""
keywords.py — DataForSEO keyword research for the consulting24.co content pipeline.
Auth (Basic, base64 login:password) from $DATAFORSEO_AUTH or scripts/.dataforseo_auth (gitignored).

  python3 scripts/keywords.py volume "kw one" "kw two" ...   # live Google Ads search volume
  python3 scripts/keywords.py ideas "seed keyword" [N]       # related keyword suggestions ranked by volume

Used by the daily pipeline to pick data-backed keywords (not guesses) and to
extend the landing-page queue with high-demand terms.
"""
import os, sys, json, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOC, LANG = 2840, "en"   # US as the reference English market

def auth():
    a = os.environ.get("DATAFORSEO_AUTH")
    if a: return a.strip()
    p = os.path.join(ROOT, "scripts", ".dataforseo_auth")
    if os.path.exists(p): return open(p).read().strip()
    sys.exit("No DataForSEO auth (set DATAFORSEO_AUTH or scripts/.dataforseo_auth)")

def post(path, payload):
    req = urllib.request.Request("https://api.dataforseo.com/v3/" + path,
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Basic " + auth(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)

def volume(keywords):
    d = post("keywords_data/google_ads/search_volume/live",
             [{"keywords": keywords, "location_code": LOC, "language_code": LANG}])
    out = []
    for t in d.get("tasks") or []:
        for r in t.get("result") or []:
            out.append((r.get("keyword"), r.get("search_volume") or 0, r.get("competition")))
    return sorted(out, key=lambda x: -(x[1] or 0))

def ideas(seed, n=40):
    d = post("dataforseo_labs/google/keyword_suggestions/live",
             [{"keyword": seed, "location_code": LOC, "language_code": LANG,
               "limit": n, "order_by": ["keyword_info.search_volume,desc"]}])
    out = []
    for t in d.get("tasks") or []:
        for res in t.get("result") or []:
            for item in res.get("items") or []:
                ki = item.get("keyword_info") or {}
                out.append((item.get("keyword"), ki.get("search_volume") or 0, ki.get("competition")))
    return out

if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "volume":
        for kw, vol, comp in volume(sys.argv[2:]):
            print(f"{vol:7}  {comp or '-':6}  {kw}")
    elif cmd == "ideas":
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 40
        for kw, vol, comp in ideas(sys.argv[2], n):
            print(f"{vol:7}  {comp or '-':6}  {kw}")
    else:
        sys.exit("cmd must be 'volume' or 'ideas'")
