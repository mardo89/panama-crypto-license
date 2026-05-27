#!/bin/bash
cd /Users/master/panama-crypto-license || exit 1
for i in 1 2 3 4; do
  echo "--- attempt $i ---"
  out=$(python3 scripts/generate.py landing estonia-crypto-license "Estonia crypto license" "Estonia | EU; Estonian Financial Supervision Authority (Finantsinspektsioon); MiCA CASP in force 2026 (replaced old FIU/VASP register); minimum capital EUR 50,000/125,000/150,000 by service class; 0% corporate tax on retained profit, 22% on distribution; ~5-9 months; e-Residency; central administration must be in Estonia; Consulting24 delivers directly. Do not over-repeat the exact phrase 'Estonia crypto license' — use natural variations to keep density under 1.6%.")
  echo "$out"
  echo "$out" | grep -q "WROTE" && break
done
if git diff --quiet estonia-crypto-license/index.html; then echo "NO CHANGE - estonia still failing"; else
  python3 scripts/publish.py >/dev/null 2>&1
  git add -A && git commit -q -m "Regenerate Estonia to QC standard (2000+ words)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
  git push origin main 2>&1 | tail -1
fi
echo "=== ESTONIA DONE ==="
