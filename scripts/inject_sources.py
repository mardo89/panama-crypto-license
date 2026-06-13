import os, re, sys, pathlib, importlib.util
ROOT = pathlib.Path(__file__).resolve().parents[1]
SKIP = {"blog","scripts","config","img","logs","jurisdictions"}
spec = importlib.util.spec_from_file_location("reg", ROOT/"scripts"/"regulators.py")
reg = importlib.util.module_from_spec(spec); spec.loader.exec_module(reg)

def targets():
    for d in sorted(os.listdir(ROOT)):
        if d in SKIP: continue
        p = ROOT/d/"index.html"
        if p.exists(): yield p, d
    for p in sorted((ROOT/"blog").glob("*/index.html")):
        yield p, p.parent.name

done = skip = 0
for p, slug in targets():
    h = p.read_text(encoding="utf-8")
    if 'class="primary-sources"' in h:
        skip += 1; continue
    block = reg.sources_block(slug)
    if not block:
        skip += 1; continue
    # insert before the footer (landing) or before </article> (fallback)
    if "<footer" in h:
        h = h.replace("<footer", block + "\n<footer", 1)
    elif "</article>" in h:
        h = h.replace("</article>", block + "\n</article>", 1)
    else:
        skip += 1; continue
    p.write_text(h, encoding="utf-8")
    done += 1
print(f"sources injected: {done} pages, {skip} skipped (no regulator / already present)")
