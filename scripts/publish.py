#!/usr/bin/env python3
"""
publish.py — regenerate sitemap.xml from all pages, refresh the blog index
card list, and ping IndexNow (Bing/Yandex) so new content is indexed fast.

Run after adding/updating blog posts:
    python3 scripts/publish.py

It is safe to run repeatedly; it derives everything from the files on disk.
"""
import os, re, json, glob, datetime, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.consulting24.co"
TODAY = datetime.date.today().isoformat()

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def title_of(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return (m.group(1).strip() if m else "").replace(" | Consulting24", "")

def first_meta_desc(html):
    m = re.search(r'<meta name="description" content="(.*?)"', html, re.S)
    return m.group(1).strip() if m else ""

# 1. Collect all pages (index.html files)
pages = []
for path in glob.glob(os.path.join(ROOT, "**", "index.html"), recursive=True):
    rel = os.path.relpath(path, ROOT)
    url_path = "" if rel == "index.html" else "/" + os.path.dirname(rel) + "/"
    pages.append((BASE + (url_path or "/"), path, url_path))

# 2. Build sitemap.xml
def priority(url_path):
    if url_path == "": return "1.0"
    if url_path.startswith("/blog"): return "0.7"
    return "0.9"

entries = []
for url, path, url_path in sorted(pages):
    lastmod = datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()
    entries.append(
        f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod>"
        f"<changefreq>weekly</changefreq><priority>{priority(url_path)}</priority></url>"
    )
sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(entries) + "\n</urlset>\n")
with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write(sitemap)
print(f"sitemap.xml: {len(pages)} URLs")

# 3. Ping IndexNow (Bing, Yandex, Seznam share the protocol)
keyfile = os.path.join(ROOT, ".indexnow-key")
if os.path.exists(keyfile):
    key = read(keyfile).strip()
    url_list = [u for (u, _, _) in pages]
    payload = json.dumps({
        "host": "www.consulting24.co",
        "key": key,
        "keyLocation": f"{BASE}/{key}.txt",
        "urlList": url_list,
    }).encode()
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"IndexNow: HTTP {r.status} for {len(url_list)} URLs")
    except Exception as e:
        print(f"IndexNow ping failed (non-fatal): {e}")
else:
    print("No .indexnow-key found; skipping IndexNow ping")

# 4. Submit sitemap to Bing Webmaster Tools via its API (SubmitFeed).
# Key from Bing Webmaster Tools > Settings > API access > API Key.
# Bing dedupes feeds, so re-submitting the same sitemap is harmless.
bing_keyfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".bing_api_key")
if os.path.exists(bing_keyfile):
    bing_key = read(bing_keyfile).strip()
    payload = json.dumps({
        "siteUrl": BASE + "/",
        "feedUrl": f"{BASE}/sitemap.xml",
    }).encode()
    req = urllib.request.Request(
        f"https://ssl.bing.com/webmaster/api.svc/json/SubmitFeed?apikey={bing_key}",
        data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"Bing SubmitFeed: HTTP {r.status} for {BASE}/sitemap.xml")
    except Exception as e:
        print(f"Bing SubmitFeed failed (non-fatal): {e}")
else:
    print("No scripts/.bing_api_key found; skipping Bing sitemap submission")
