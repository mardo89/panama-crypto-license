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
    ref_path = os.path.join(ROOT, "data", "jurisdictions.json")
    ref = json.load(open(ref_path, encoding="utf-8"))["jurisdictions"] if os.path.exists(ref_path) else []
    ref_by = {r["slug"]: r for r in ref}
    op_by = {j["slug"]: j for j in cfg["jurisdictions"]}

    # Always emit the endpoint: REFERENCE facts (published, verified) as the base, plus the
    # OPERATOR layer per jurisdiction ONLY where real data is filled (never fabricated).
    jur = []
    n_op = 0
    for slug, r in ref_by.items():
        j = op_by.get(slug, {})
        row = {"slug": slug, "name": r.get("name"), "service_model": r.get("service_model"),
               "regulator": r.get("regulator"), "reference_timeline": r.get("timeline")}
        if filled(j):
            n_op += 1
            row["operator"] = {k: j[k] for k in ("sample_size", "period", "setup_cost_eur",
                               "timeline_weeks", "approval_rate_pct", "top_rejection_reasons", "notes")
                               if j.get(k) not in (None, [], "")}
        jur.append(row)

    out = {
        "name": cfg.get("index_name"), "edition": cfg.get("edition"),
        "source": "Consulting24 (X24Consulting OU, reg 16971898, Tallinn)",
        "total_deliveries": cfg.get("total_deliveries"),
        "methodology": cfg.get("methodology_url"), "disclaimer": cfg.get("disclaimer"),
        "note": ("Base rows are verified 2026 regulatory reference facts. The 'operator' object "
                 "(aggregated data from real Consulting24 deliveries) is present only where filled; "
                 "absence means that jurisdiction's operator data is still being compiled."),
        "jurisdictions": jur,
    }
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "licensing-index.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"data/licensing-index.json: {len(jur)} jurisdictions (reference); "
          f"{n_op} with real operator data filled" + ("" if n_op else " — fill config/licensing_index.json to enrich"))

if __name__ == "__main__":
    main()
