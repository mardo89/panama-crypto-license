#!/usr/bin/env python3
"""Emit /data/jurisdictions.json — one machine-readable source of truth for LLMs and
agents, derived from the authoritative FACTS dict in daily_run.py. Linked from llms.txt.
Run in the daily pipeline (before publish) so it stays fresh.
"""
import json, os, re
from importlib.util import spec_from_file_location, module_from_spec

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = spec_from_file_location("dr", os.path.join(ROOT, "scripts", "daily_run.py"))
dr = module_from_spec(_spec); _spec.loader.exec_module(dr)

BUILD_DATE = "2026-07-21"   # bump on data changes (kept static: no Date.now in pipeline determinism)

def model_of(low):
    if "comparison-only" in low: return "comparison-only"
    if "delivers" in low and "directly" in low: return "direct"   # "delivers directly" / "delivers Panama directly"
    return "advise-and-coordinate"

def parse(slug, txt):
    name, rest = (txt.split("|", 1) + [""])[:2]
    name, rest = name.strip(), rest.strip()
    segs = [s.strip() for s in rest.split(";") if s.strip()]
    low = rest.lower()
    tl = re.search(r"~?\s*(\d+\s*[-–]\s*\d+\s*(?:months|weeks)|\d+\s*(?:months|weeks))", rest, re.I)
    page = "/" if slug == "panama" else (
        f"/{slug}-crypto-license/" if os.path.exists(os.path.join(ROOT, f"{slug}-crypto-license", "index.html"))
        else "/jurisdictions/")
    return {
        "slug": slug,
        "name": name,
        "service_model": model_of(low),
        "regulator": segs[0] if segs else None,
        "timeline": tl.group(1) if tl else None,
        "facts": segs,
        "page": "https://www.consulting24.co" + page,
        "updated": BUILD_DATE,
    }

data = {
    "source": "Consulting24 (X24Consulting OU, reg 16971898, Tallinn)",
    "note": "Panama has NO enacted crypto/VASP licence (draft Anteproyecto 314 pending). "
            "DASP/CNAD/Ley de Activos Digitales belong to El Salvador, not Panama. "
            "service_model: direct = Consulting24 sets up and files; advise-and-coordinate = we guide "
            "and coordinate local partners; comparison-only = we do NOT provide that licence.",
    "updated": BUILD_DATE,
    "jurisdictions": [parse(s, t) for s, t in dr.FACTS.items()],
}

os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
out = os.path.join(ROOT, "data", "jurisdictions.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"data/jurisdictions.json: {len(data['jurisdictions'])} jurisdictions")
