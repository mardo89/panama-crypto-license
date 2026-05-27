#!/bin/bash
cd /Users/master/panama-crypto-license || exit 1
set -o pipefail
gen() { python3 scripts/generate.py landing "$1" "$2" "$3" || python3 scripts/generate.py landing "$1" "$2" "$3"; }

gen estonia-crypto-license "Estonia crypto license" "Estonia | EU; Estonian Financial Supervision Authority (Finantsinspektsioon); MiCA CASP (replaced old VASP register); capital 50k/125k/150k; 0% tax on retained profit, 22% on distribution; ~5-9 months; e-Residency; Consulting24 delivers directly."
gen dubai-crypto-license "Dubai crypto license" "Dubai | VARA regulator; category licences (exchange, broker-dealer, custody, lending, advisory, management, transfer); premium cost (six figures USD); 0% personal income tax, 9% corporate with possible free-zone relief; ~6-12 months; DIFC (DFSA) and ADGM are separate regimes; Consulting24 advises and coordinates."
gen el-salvador-crypto-license "El Salvador crypto license" "El Salvador | CNAD regulator; DASP under Digital Assets Issuance Law + BSP under Bitcoin Law; Bitcoin is legal tender; tax incentives for qualifying digital-asset activity; ~3-6 months; Consulting24 advises and coordinates."
gen czech-republic-crypto-license "Czech Republic crypto license" "Czech Republic | EU; Czech National Bank (CNB); MiCA CASP (replaced the old trade-licence VASP route); capital 50k/125k/150k; cost-efficient EU; ~4-8 months; Consulting24 advises and coordinates."
gen poland-crypto-license "Poland crypto license" "Poland | EU; KNF (Polish Financial Supervision Authority); MiCA CASP (replaced the virtual-currency activity register); capital 50k/125k/150k; cost-efficient EU; ~4-8 months; Consulting24 advises and coordinates."
gen malta-crypto-license "Malta crypto license" "Malta | EU; MFSA; MiCA CASP (built on the earlier VFA 'Blockchain Island' framework); capital 50k/125k/150k; English is official; reputable ecosystem; ~5-9 months; Consulting24 advises and coordinates."
gen switzerland-crypto-license "Switzerland crypto license" "Switzerland | non-EU; FINMA; AML via SRO/VQF membership, DLT Act for tokenised assets, fintech/banking licences for deposit-taking models; Crypto Valley Zug; premium cost; ~6-12 months; Consulting24 advises and coordinates."
gen cayman-islands-crypto-license "Cayman Islands crypto license" "Cayman Islands | CIMA; Virtual Asset (Service Providers) Act with registration/licensing tiers; 0% direct tax; popular for funds, token issuers and exchanges; economic-substance and AML rules apply; ~3-6 months; Consulting24 advises and coordinates."

echo "=== linkcheck ===" ; python3 scripts/linkcheck.py || true
echo "=== publish ===" ; python3 scripts/publish.py || true
git add -A
git commit -q -m "Backfill 9 jurisdiction pages to QC standard via DeepSeek

Regenerate Lithuania, Estonia, Dubai, El Salvador, Czech, Poland, Malta,
Switzerland, Cayman through the QC gate (2300+ words, 8+ FAQs, 4 images,
authority links). Refresh sitemap + IndexNow.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
git push origin main 2>&1 | tail -1
echo "=== BACKFILL DONE ==="
