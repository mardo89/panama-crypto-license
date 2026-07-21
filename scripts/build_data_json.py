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

# FACTS doubles as the generator's prompt brief, so some sentences are model guardrails
# ("DO NOT invent a Panama crypto law...") rather than citable facts. They must never reach
# the public JSON that llms.txt advertises to AI crawlers.
_DIRECTIVE = re.compile(r"\bDO NOT\b")

def _citable(seg):
    """Drop model-directive sentences from a fact segment; keep the real facts."""
    parts = re.split(r"(?<=[.])\s+", seg)
    kept = [p for p in parts if not _DIRECTIVE.search(p)]
    return " ".join(kept).strip(" .;") or None

# segs[0] is normally the regulator, but not always: Panama leads with a full sentence (and
# has no regulator that issues a crypto licence), Switzerland leads with "non-EU".
REGULATOR_OVERRIDE = {"panama": None, "switzerland": "FINMA"}

def _regulator(slug, segs):
    if slug in REGULATOR_OVERRIDE:
        return REGULATOR_OVERRIDE[slug]
    if not segs:
        return None
    first = segs[0]
    # a sentence is a description, not a regulator name
    if len(first) > 70 or re.search(r"[.]\s+[A-Z]", first):
        return None
    return first

def parse(slug, txt):
    name, rest = (txt.split("|", 1) + [""])[:2]
    name, rest = name.strip(), rest.strip()
    segs = [c for c in (_citable(s.strip()) for s in rest.split(";") if s.strip()) if c]
    low = rest.lower()
    tl = re.search(r"~?\s*(\d+\s*[-–]\s*\d+\s*(?:months|weeks)|\d+\s*(?:months|weeks))", rest, re.I)
    page = "/" if slug == "panama" else (
        f"/{slug}-crypto-license/" if os.path.exists(os.path.join(ROOT, f"{slug}-crypto-license", "index.html"))
        else "/jurisdictions/")
    return {
        "slug": slug,
        "name": name,
        "service_model": model_of(low),
        "regulator": _regulator(slug, segs),
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
