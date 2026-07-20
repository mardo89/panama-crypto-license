#!/usr/bin/env python3
"""Build the public Consulting24 Crypto Licensing Index from REAL delivery data.

Reads config/licensing_index.json (owner fills it with anonymized delivery numbers),
validates, and emits:
  - /data/licensing-index.json   (machine-readable; linked from llms.txt for AI citation)
Only jurisdictions with a real sample_size (>0) AND filled cost+timeline are published;
placeholder (null) rows are skipped, so nothing fabricated ever ships. If no jurisdiction
is filled yet, it publishes nothing and tells you what to fill.

The Index is the strategic moat (SEO strategy 2026-07-21): proprietary first-party data
that earns editorial links + AI citations, which law firms and content farms cannot copy.

Usage: python3 scripts/build_licensing_index.py
"""
from __future__ import annotations
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, "config", "licensing_index.json")
BASE = "https://www.consulting24.co"

def filled(j):
    c, t = j.get("setup_cost_eur") or {}, j.get("timeline_weeks") or {}
    return bool(j.get("sample_size")) and c.get("typical") is not None and t.get("typical") is not None

def main():
    if not os.path.exists(CFG):
        sys.exit(f"missing {CFG} — run the scaffold first")
    cfg = json.load(open(CFG, encoding="utf-8"))
    ready = [j for j in cfg["jurisdictions"] if filled(j)]
    pending = [j["slug"] for j in cfg["jurisdictions"] if not filled(j)]
    if not ready:
        print("Licensing Index: 0 jurisdictions filled yet — nothing published (no fabricated data).")
        print("  Fill sample_size + setup_cost_eur.typical + timeline_weeks.typical in "
              "config/licensing_index.json for at least Panama/Estonia/Lithuania, then re-run.")
        return
    out = {
        "name": cfg.get("index_name"),
        "edition": cfg.get("edition"),
        "source": "Consulting24 (X24Consulting OU, reg 16971898, Tallinn)",
        "total_deliveries": cfg.get("total_deliveries"),
        "methodology": cfg.get("methodology_url"),
        "disclaimer": cfg.get("disclaimer"),
        "jurisdictions": [
            {k: j[k] for k in ("slug", "name", "service_model", "sample_size", "period",
                               "setup_cost_eur", "timeline_weeks", "approval_rate_pct",
                               "top_rejection_reasons", "notes") if k in j}
            for j in ready
        ],
    }
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "licensing-index.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"data/licensing-index.json: {len(ready)} jurisdictions published; "
          f"{len(pending)} still placeholder ({', '.join(pending[:6])}{'...' if len(pending) > 6 else ''}).")

if __name__ == "__main__":
    main()
