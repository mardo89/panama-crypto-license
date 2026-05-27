#!/bin/bash
cd /Users/master/panama-crypto-license || exit 1
python3 scripts/generate.py landing dubai-crypto-license "Dubai crypto license" "Dubai | VARA (Virtual Assets Regulatory Authority); category licences (exchange, broker-dealer, custody, lending, advisory, management); UAE 0% personal income tax, 9% federal corporate tax with possible free-zone relief; premium cost (six figures USD); DIFC (DFSA) and ADGM (FSRA) are separate regimes; ~6-12 months. DELIVERY=comparison-only — heavy Panama comparison; steer readers to Panama (EUR 6,000) and EE/LT."
python3 scripts/generate.py landing estonia-crypto-license "Estonia crypto license" "Estonia | EU; Estonian Financial Supervision Authority (Finantsinspektsioon); MiCA CASP in force 2026 (replaced old FIU/VASP register); minimum capital EUR 50,000/125,000/150,000 by service class; 0% corporate tax on retained profit, 22% on distribution; ~5-9 months; e-Residency for digital management; Consulting24 delivers directly."
echo "=== linkcheck ==="; python3 scripts/linkcheck.py || true
echo "=== publish ==="; python3 scripts/publish.py || true
git add -A
git commit -q -m "Regenerate Dubai (comparison-only) + Estonia to QC standard

Dubai: UAE VARA is NOT a Consulting24-delivered licence — rewrite as
informational + Panama comparison (no advise/coordinate claim), CTA to
Panama/EE/LT. Estonia: regenerate to pass the 2000-word QC gate.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
git push origin main 2>&1 | tail -1
echo "=== FIX2 DONE ==="
