# Prune candidate report (READ-ONLY — no changes made)

Classification of all 943 real (indexable) pages against the strategy test: *do we have
first-hand delivery experience or genuine comparison value on this page?* Heuristic only —
**there is no GSC/impression data yet**, so treat this as candidates to VERIFY, not a delete list.

## Tally
| Tier | Count | Meaning |
|---|---|---|
| KEEP (money/hub/direct/decision) | 156 | core — never prune |
| KEEP-hub (advise-jurisdiction hubs) | 18 | real coverage — keep, enrich with operator data |
| KEEP-blog (core/decision topics) | 175 | keep |
| REVIEW | 177 | activity pages for advise jurisdictions + non-core comparisons — decide with impression data |
| REVIEW-blog | 150 | non-core blog posts — decide with impression data |
| **PRUNE-CANDIDATE** | **267** | **no first-hand delivery + zero visibility — Wave-1 candidates** |

**Clear KEEP: 349  ·  Clear PRUNE-CANDIDATE: 267  ·  REVIEW (needs data): 327**

## Guardrails (do NOT skip)
1. **Verify before executing.** Pull GSC/Bing impressions + backlinks per URL first. Any page with
   real impressions or an external backlink comes OFF this list.
2. **301, never delete.** Redirect each candidate to the mapped hub (below) so any equity is preserved;
   the existing `config/redirects.json` + `scripts/redirects.py` mechanism handles it.
3. **Phase it.** Execute Wave 1 (the 267 clear candidates), re-measure for 3-4 weeks, THEN decide the
   327 REVIEW bucket. The strategist end-state (~60-90 pages) is only justified if the data supports it.
4. Keep the reciprocal internal links pointing at survivors, not at redirected URLs (rebuild after).

## Wave 1 — prune candidates by 301 target

### → 301 to /jurisdictions/  (100 pages)
- `/anjouan-crypto-license/`  _(inbound 11, 3697w)_
- `/belize-crypto-license/`  _(inbound 11, 3142w)_
- `/bermuda-crypto-license/`  _(inbound 7, 3886w)_
- `/bulgaria-crypto-license/`  _(inbound 9, 3034w)_
- `/croatia-crypto-license/`  _(inbound 2, 3075w)_
- `/crypto-broker-license-bahrain/`  _(inbound 17, 3694w)_
- `/crypto-broker-license-indonesia/`  _(inbound 7, 3794w)_
- `/crypto-broker-license-jersey/`  _(inbound 10, 3038w)_
- `/crypto-broker-license-kazakhstan/`  _(inbound 10, 3016w)_
- `/crypto-broker-license-turkey/`  _(inbound 11, 3224w)_
- `/crypto-fund-license-bahrain/`  _(inbound 19, 3342w)_
- `/crypto-fund-license-indonesia/`  _(inbound 3, 2981w)_
- `/crypto-fund-license-jersey/`  _(inbound 10, 3162w)_
- `/crypto-fund-license-kazakhstan/`  _(inbound 10, 3367w)_
- `/crypto-fund-license-liechtenstein/`  _(inbound 11, 3586w)_
- `/crypto-fund-license-luxembourg/`  _(inbound 9, 3050w)_
- `/crypto-fund-license-philippines/`  _(inbound 8, 3100w)_
- `/crypto-fund-license-turkey/`  _(inbound 11, 3424w)_
- `/crypto-gambling-license-bahrain/`  _(inbound 15, 3046w)_
- `/crypto-gambling-license-japan/`  _(inbound 4, 3317w)_
- `/crypto-gambling-license-jersey/`  _(inbound 9, 3169w)_
- `/crypto-gambling-license-kazakhstan/`  _(inbound 6, 3687w)_
- `/crypto-gambling-license-liechtenstein/`  _(inbound 10, 3278w)_
- `/crypto-gambling-license-philippines/`  _(inbound 8, 3628w)_
- `/crypto-gambling-license-thailand/`  _(inbound 6, 3214w)_
- `/crypto-gambling-license-turkey/`  _(inbound 7, 3162w)_
- `/crypto-nft-marketplace-license-bahrain/`  _(inbound 40, 3434w)_
- `/crypto-nft-marketplace-license-indonesia/`  _(inbound 2, 3852w)_
- `/crypto-nft-marketplace-license-jersey/`  _(inbound 6, 3074w)_
- `/crypto-nft-marketplace-license-kazakhstan/`  _(inbound 4, 3349w)_
- `/crypto-nft-marketplace-license-liechtenstein/`  _(inbound 11, 3248w)_
- `/crypto-nft-marketplace-license-luxembourg/`  _(inbound 9, 3150w)_
- `/crypto-nft-marketplace-license-philippines/`  _(inbound 6, 3822w)_
- `/crypto-nft-marketplace-license-thailand/`  _(inbound 6, 3491w)_
- `/crypto-nft-marketplace-license-turkey/`  _(inbound 5, 3574w)_
- `/crypto-otc-desk-license-bahrain/`  _(inbound 37, 3404w)_
- `/crypto-otc-desk-license-indonesia/`  _(inbound 5, 3252w)_
- `/crypto-otc-desk-license-jersey/`  _(inbound 5, 3499w)_
- `/crypto-otc-desk-license-kazakhstan/`  _(inbound 4, 3811w)_
- `/crypto-otc-desk-license-liechtenstein/`  _(inbound 8, 3525w)_
- `/crypto-otc-desk-license-luxembourg/`  _(inbound 10, 3327w)_
- `/crypto-otc-desk-license-philippines/`  _(inbound 3, 3130w)_
- `/crypto-otc-desk-license-turkey/`  _(inbound 5, 3378w)_
- `/crypto-payment-institution-license-bahrain/`  _(inbound 12, 3477w)_
- `/crypto-payment-institution-license-indonesia/`  _(inbound 1, 3252w)_
- `/crypto-payment-institution-license-jersey/`  _(inbound 4, 3255w)_
- `/crypto-payment-institution-license-kazakhstan/`  _(inbound 3, 3326w)_
- `/crypto-payment-institution-license-liechtenstein/`  _(inbound 5, 3606w)_
- `/crypto-payment-institution-license-luxembourg/`  _(inbound 5, 2985w)_
- `/crypto-payment-institution-license-philippines/`  _(inbound 2, 3348w)_
- `/crypto-payment-institution-license-thailand/`  _(inbound 6, 3078w)_
- `/crypto-payment-institution-license-turkey/`  _(inbound 4, 3882w)_
- `/crypto-staking-license-bahrain/`  _(inbound 36, 3758w)_
- `/crypto-staking-license-japan/`  _(inbound 4, 3292w)_
- `/crypto-staking-license-liechtenstein/`  _(inbound 4, 3173w)_
- `/crypto-staking-license-luxembourg/`  _(inbound 4, 3486w)_
- `/crypto-staking-license-thailand/`  _(inbound 2, 3052w)_
- `/crypto-staking-license-turkey/`  _(inbound 2, 3168w)_
- `/crypto-token-issuance-license-bahrain/`  _(inbound 8, 3681w)_
- `/crypto-token-issuance-license-japan/`  _(inbound 4, 3087w)_
- `/crypto-token-issuance-license-jersey/`  _(inbound 3, 3359w)_
- `/crypto-token-issuance-license-kazakhstan/`  _(inbound 1, 3258w)_
- `/crypto-token-issuance-license-liechtenstein/`  _(inbound 3, 3112w)_
- `/crypto-token-issuance-license-luxembourg/`  _(inbound 3, 3154w)_
- `/crypto-token-issuance-license-thailand/`  _(inbound 1, 3359w)_
- `/crypto-token-issuance-license-turkey/`  _(inbound 1, 3451w)_
- `/crypto-wallet-custody-license-bahrain/`  _(inbound 33, 3146w)_
- `/crypto-wallet-custody-license-indonesia/`  _(inbound 4, 3290w)_
- `/crypto-wallet-custody-license-kazakhstan/`  _(inbound 1, 3369w)_
- `/crypto-wallet-custody-license-liechtenstein/`  _(inbound 1, 3684w)_
- `/crypto-wallet-custody-license-luxembourg/`  _(inbound 1, 3033w)_
- `/crypto-wallet-custody-license-philippines/`  _(inbound 1, 3542w)_
- `/crypto-wallet-custody-license-turkey/`  _(inbound 1, 3161w)_
- `/easiest-crypto-license/`  _(inbound 2, 3651w)_
- `/fastest-crypto-license/`  _(inbound 8, 3143w)_
- `/france-crypto-license/`  _(inbound 3, 3591w)_
- `/germany-crypto-license/`  _(inbound 13, 3152w)_
- `/greece-crypto-license/`  _(inbound 2, 3299w)_
- `/how-to-get-a-crypto-license/`  _(inbound 3, 3666w)_
- `/hungary-crypto-license/`  _(inbound 1, 3292w)_
- `/ireland-crypto-license/`  _(inbound 12, 4018w)_
- `/isle-of-man-crypto-license/`  _(inbound 12, 3815w)_
- `/italy-crypto-license/`  _(inbound 1, 3335w)_
- `/labuan-crypto-license/`  _(inbound 12, 3804w)_
- `/latvia-crypto-license/`  _(inbound 1, 3364w)_
- `/marshall-islands-crypto-license/`  _(inbound 5, 4358w)_
- `/netherlands-crypto-license/`  _(inbound 2, 3258w)_
- `/portugal-crypto-license/`  _(inbound 11, 3363w)_
- `/qatar-crypto-license/`  _(inbound 10, 3006w)_
- `/ready-made-crypto-license/`  _(inbound 2, 3850w)_
- `/romania-crypto-license/`  _(inbound 10, 3047w)_
- `/saint-lucia-crypto-license/`  _(inbound 10, 3062w)_
- `/saudi-arabia-crypto-license/`  _(inbound 7, 3108w)_
- `/slovakia-crypto-license/`  _(inbound 7, 3115w)_
- `/south-africa-crypto-license/`  _(inbound 12, 3402w)_
- `/south-korea-crypto-license/`  _(inbound 13, 3707w)_
- `/spain-crypto-license/`  _(inbound 1, 3600w)_
- `/uae-crypto-license/`  _(inbound 3, 3025w)_
- `/usa-crypto-license/`  _(inbound 14, 3007w)_
- `/vanuatu-crypto-license/`  _(inbound 3, 3783w)_

### → 301 to /usa-crypto-license/  (11 pages)
- `/crypto-broker-license-usa/`  _(inbound 12, 3378w)_
- `/crypto-exchange-license-usa/`  _(inbound 12, 3478w)_
- `/crypto-fund-license-usa/`  _(inbound 13, 3337w)_
- `/crypto-gambling-license-usa/`  _(inbound 4, 3931w)_
- `/crypto-nft-marketplace-license-usa/`  _(inbound 3, 3156w)_
- `/crypto-otc-desk-license-usa/`  _(inbound 3, 3056w)_
- `/crypto-payment-institution-license-usa/`  _(inbound 2, 3383w)_
- `/crypto-stablecoin-license-usa/`  _(inbound 2, 3414w)_
- `/crypto-staking-license-usa/`  _(inbound 2, 3570w)_
- `/crypto-token-issuance-license-usa/`  _(inbound 2, 3342w)_
- `/crypto-wallet-custody-license-usa/`  _(inbound 1, 3672w)_

### → 301 to /isle-of-man-crypto-license/  (11 pages)
- `/crypto-broker-license-isle-of-man/`  _(inbound 12, 3414w)_
- `/crypto-exchange-license-isle-of-man/`  _(inbound 12, 3312w)_
- `/crypto-fund-license-isle-of-man/`  _(inbound 13, 3673w)_
- `/crypto-gambling-license-isle-of-man/`  _(inbound 12, 3904w)_
- `/crypto-nft-marketplace-license-isle-of-man/`  _(inbound 8, 3795w)_
- `/crypto-otc-desk-license-isle-of-man/`  _(inbound 8, 3330w)_
- `/crypto-payment-institution-license-isle-of-man/`  _(inbound 8, 3056w)_
- `/crypto-stablecoin-license-isle-of-man/`  _(inbound 5, 3396w)_
- `/crypto-staking-license-isle-of-man/`  _(inbound 6, 3238w)_
- `/crypto-token-issuance-license-isle-of-man/`  _(inbound 5, 3244w)_
- `/crypto-wallet-custody-license-isle-of-man/`  _(inbound 2, 3180w)_

### → 301 to /south-korea-crypto-license/  (11 pages)
- `/crypto-broker-license-south-korea/`  _(inbound 11, 3348w)_
- `/crypto-exchange-license-south-korea/`  _(inbound 11, 3360w)_
- `/crypto-fund-license-south-korea/`  _(inbound 11, 3732w)_
- `/crypto-gambling-license-south-korea/`  _(inbound 7, 3873w)_
- `/crypto-nft-marketplace-license-south-korea/`  _(inbound 5, 3290w)_
- `/crypto-otc-desk-license-south-korea/`  _(inbound 5, 3084w)_
- `/crypto-payment-institution-license-south-korea/`  _(inbound 4, 3324w)_
- `/crypto-stablecoin-license-south-korea/`  _(inbound 1, 3613w)_
- `/crypto-staking-license-south-korea/`  _(inbound 1, 3286w)_
- `/crypto-token-issuance-license-south-korea/`  _(inbound 1, 3432w)_
- `/crypto-wallet-custody-license-south-korea/`  _(inbound 1, 3321w)_

### → 301 to /ireland-crypto-license/  (11 pages)
- `/crypto-broker-license-ireland/`  _(inbound 16, 3290w)_
- `/crypto-exchange-license-ireland/`  _(inbound 12, 3311w)_
- `/crypto-fund-license-ireland/`  _(inbound 13, 3184w)_
- `/crypto-gambling-license-ireland/`  _(inbound 12, 3235w)_
- `/crypto-nft-marketplace-license-ireland/`  _(inbound 8, 3246w)_
- `/crypto-otc-desk-license-ireland/`  _(inbound 9, 3731w)_
- `/crypto-payment-institution-license-ireland/`  _(inbound 7, 3159w)_
- `/crypto-stablecoin-license-ireland/`  _(inbound 5, 3557w)_
- `/crypto-staking-license-ireland/`  _(inbound 6, 3038w)_
- `/crypto-token-issuance-license-ireland/`  _(inbound 5, 3718w)_
- `/crypto-wallet-custody-license-ireland/`  _(inbound 2, 3762w)_

### → 301 to /germany-crypto-license/  (11 pages)
- `/crypto-broker-license-germany/`  _(inbound 36, 3244w)_
- `/crypto-exchange-license-germany/`  _(inbound 20, 3291w)_
- `/crypto-fund-license-germany/`  _(inbound 19, 3839w)_
- `/crypto-gambling-license-germany/`  _(inbound 20, 3134w)_
- `/crypto-nft-marketplace-license-germany/`  _(inbound 12, 3179w)_
- `/crypto-otc-desk-license-germany/`  _(inbound 14, 3413w)_
- `/crypto-payment-institution-license-germany/`  _(inbound 9, 3223w)_
- `/crypto-stablecoin-license-germany/`  _(inbound 5, 3532w)_
- `/crypto-staking-license-germany/`  _(inbound 9, 3241w)_
- `/crypto-token-issuance-license-germany/`  _(inbound 5, 3328w)_
- `/crypto-wallet-custody-license-germany/`  _(inbound 5, 3108w)_

### → 301 to /labuan-crypto-license/  (11 pages)
- `/crypto-broker-license-labuan/`  _(inbound 13, 3072w)_
- `/crypto-exchange-license-labuan/`  _(inbound 12, 2966w)_
- `/crypto-fund-license-labuan/`  _(inbound 13, 3632w)_
- `/crypto-gambling-license-labuan/`  _(inbound 12, 3157w)_
- `/crypto-nft-marketplace-license-labuan/`  _(inbound 9, 3426w)_
- `/crypto-otc-desk-license-labuan/`  _(inbound 9, 3595w)_
- `/crypto-payment-institution-license-labuan/`  _(inbound 7, 3724w)_
- `/crypto-stablecoin-license-labuan/`  _(inbound 5, 3434w)_
- `/crypto-staking-license-labuan/`  _(inbound 5, 3378w)_
- `/crypto-token-issuance-license-labuan/`  _(inbound 5, 3302w)_
- `/crypto-wallet-custody-license-labuan/`  _(inbound 2, 3620w)_

### → 301 to /south-africa-crypto-license/  (10 pages)
- `/crypto-broker-license-south-africa/`  _(inbound 34, 3414w)_
- `/crypto-exchange-license-south-africa/`  _(inbound 32, 4259w)_
- `/crypto-fund-license-south-africa/`  _(inbound 32, 3154w)_
- `/crypto-gambling-license-south-africa/`  _(inbound 27, 3350w)_
- `/crypto-nft-marketplace-license-south-africa/`  _(inbound 22, 3297w)_
- `/crypto-otc-desk-license-south-africa/`  _(inbound 20, 3761w)_
- `/crypto-stablecoin-license-south-africa/`  _(inbound 8, 3525w)_
- `/crypto-staking-license-south-africa/`  _(inbound 6, 3052w)_
- `/crypto-token-issuance-license-south-africa/`  _(inbound 5, 3629w)_
- `/crypto-wallet-custody-license-south-africa/`  _(inbound 3, 3409w)_

### → 301 to /portugal-crypto-license/  (10 pages)
- `/crypto-broker-license-portugal/`  _(inbound 12, 3425w)_
- `/crypto-exchange-license-portugal/`  _(inbound 11, 3283w)_
- `/crypto-fund-license-portugal/`  _(inbound 14, 3278w)_
- `/crypto-gambling-license-portugal/`  _(inbound 11, 3399w)_
- `/crypto-nft-marketplace-license-portugal/`  _(inbound 8, 3206w)_
- `/crypto-otc-desk-license-portugal/`  _(inbound 8, 3338w)_
- `/crypto-payment-institution-license-portugal/`  _(inbound 6, 3449w)_
- `/crypto-stablecoin-license-portugal/`  _(inbound 6, 3515w)_
- `/crypto-staking-license-portugal/`  _(inbound 3, 3482w)_
- `/crypto-token-issuance-license-portugal/`  _(inbound 2, 3192w)_

### → 301 to /romania-crypto-license/  (9 pages)
- `/crypto-broker-license-romania/`  _(inbound 11, 3324w)_
- `/crypto-exchange-license-romania/`  _(inbound 11, 3776w)_
- `/crypto-fund-license-romania/`  _(inbound 13, 4248w)_
- `/crypto-gambling-license-romania/`  _(inbound 10, 3346w)_
- `/crypto-nft-marketplace-license-romania/`  _(inbound 7, 3469w)_
- `/crypto-otc-desk-license-romania/`  _(inbound 7, 3044w)_
- `/crypto-payment-institution-license-romania/`  _(inbound 5, 3280w)_
- `/crypto-stablecoin-license-romania/`  _(inbound 4, 3393w)_
- `/crypto-token-issuance-license-romania/`  _(inbound 2, 3203w)_

### → 301 to /exchange-license/  (9 pages)
- `/crypto-exchange-license-bahrain/`  _(inbound 19, 3159w)_
- `/crypto-exchange-license-indonesia/`  _(inbound 7, 3446w)_
- `/crypto-exchange-license-japan/`  _(inbound 4, 3102w)_
- `/crypto-exchange-license-jersey/`  _(inbound 9, 3524w)_
- `/crypto-exchange-license-kazakhstan/`  _(inbound 10, 4034w)_
- `/crypto-exchange-license-liechtenstein/`  _(inbound 11, 3404w)_
- `/crypto-exchange-license-luxembourg/`  _(inbound 9, 3222w)_
- `/crypto-exchange-license-philippines/`  _(inbound 8, 3615w)_
- `/crypto-exchange-license-turkey/`  _(inbound 11, 3482w)_

### → 301 to /saint-lucia-crypto-license/  (9 pages)
- `/crypto-broker-license-saint-lucia/`  _(inbound 9, 3329w)_
- `/crypto-exchange-license-saint-lucia/`  _(inbound 9, 3232w)_
- `/crypto-fund-license-saint-lucia/`  _(inbound 9, 3434w)_
- `/crypto-otc-desk-license-saint-lucia/`  _(inbound 8, 3571w)_
- `/crypto-payment-institution-license-saint-lucia/`  _(inbound 4, 3041w)_
- `/crypto-stablecoin-license-saint-lucia/`  _(inbound 1, 3690w)_
- `/crypto-staking-license-saint-lucia/`  _(inbound 2, 3558w)_
- `/crypto-token-issuance-license-saint-lucia/`  _(inbound 1, 3170w)_
- `/crypto-wallet-custody-license-saint-lucia/`  _(inbound 1, 3134w)_

### → 301 to /belize-crypto-license/  (8 pages)
- `/crypto-broker-license-belize/`  _(inbound 14, 3819w)_
- `/crypto-exchange-license-belize/`  _(inbound 16, 3990w)_
- `/crypto-fund-license-belize/`  _(inbound 16, 4539w)_
- `/crypto-gambling-license-belize/`  _(inbound 14, 3149w)_
- `/crypto-nft-marketplace-license-belize/`  _(inbound 15, 3150w)_
- `/crypto-payment-institution-license-belize/`  _(inbound 11, 3795w)_
- `/crypto-stablecoin-license-belize/`  _(inbound 9, 3029w)_
- `/crypto-staking-license-belize/`  _(inbound 9, 3661w)_

### → 301 to /anjouan-crypto-license/  (8 pages)
- `/crypto-broker-license-anjouan/`  _(inbound 40, 3152w)_
- `/crypto-exchange-license-anjouan/`  _(inbound 50, 3852w)_
- `/crypto-fund-license-anjouan/`  _(inbound 46, 3409w)_
- `/crypto-gambling-license-anjouan/`  _(inbound 48, 3568w)_
- `/crypto-otc-desk-license-anjouan/`  _(inbound 41, 3581w)_
- `/crypto-payment-institution-license-anjouan/`  _(inbound 46, 3047w)_
- `/crypto-stablecoin-license-anjouan/`  _(inbound 43, 4237w)_
- `/crypto-token-issuance-license-anjouan/`  _(inbound 42, 2966w)_

### → 301 to /qatar-crypto-license/  (8 pages)
- `/crypto-broker-license-qatar/`  _(inbound 8, 3193w)_
- `/crypto-exchange-license-qatar/`  _(inbound 8, 3368w)_
- `/crypto-fund-license-qatar/`  _(inbound 8, 3606w)_
- `/crypto-gambling-license-qatar/`  _(inbound 5, 3062w)_
- `/crypto-nft-marketplace-license-qatar/`  _(inbound 3, 3627w)_
- `/crypto-payment-institution-license-qatar/`  _(inbound 2, 3463w)_
- `/crypto-staking-license-qatar/`  _(inbound 1, 3817w)_
- `/crypto-wallet-custody-license-qatar/`  _(inbound 1, 3149w)_

### → 301 to /saudi-arabia-crypto-license/  (6 pages)
- `/crypto-fund-license-saudi-arabia/`  _(inbound 6, 2993w)_
- `/crypto-nft-marketplace-license-saudi-arabia/`  _(inbound 6, 3171w)_
- `/crypto-payment-institution-license-saudi-arabia/`  _(inbound 6, 3345w)_
- `/crypto-stablecoin-license-saudi-arabia/`  _(inbound 4, 3267w)_
- `/crypto-staking-license-saudi-arabia/`  _(inbound 2, 3667w)_
- `/crypto-token-issuance-license-saudi-arabia/`  _(inbound 1, 3427w)_

### → 301 to /slovakia-crypto-license/  (6 pages)
- `/crypto-gambling-license-slovakia/`  _(inbound 7, 3343w)_
- `/crypto-nft-marketplace-license-slovakia/`  _(inbound 8, 3094w)_
- `/crypto-payment-institution-license-slovakia/`  _(inbound 8, 3236w)_
- `/crypto-stablecoin-license-slovakia/`  _(inbound 8, 3250w)_
- `/crypto-staking-license-slovakia/`  _(inbound 3, 3914w)_
- `/crypto-token-issuance-license-slovakia/`  _(inbound 2, 3534w)_

### → 301 to /bulgaria-crypto-license/  (6 pages)
- `/crypto-broker-license-bulgaria/`  _(inbound 38, 3105w)_
- `/crypto-exchange-license-bulgaria/`  _(inbound 48, 3902w)_
- `/crypto-otc-desk-license-bulgaria/`  _(inbound 42, 3046w)_
- `/crypto-stablecoin-license-bulgaria/`  _(inbound 42, 2995w)_
- `/crypto-token-issuance-license-bulgaria/`  _(inbound 27, 3525w)_
- `/crypto-wallet-custody-license-bulgaria/`  _(inbound 23, 3274w)_

### → 301 to /stablecoin-license/  (5 pages)
- `/crypto-stablecoin-license-jersey/`  _(inbound 2, 2944w)_
- `/crypto-stablecoin-license-kazakhstan/`  _(inbound 1, 3476w)_
- `/crypto-stablecoin-license-philippines/`  _(inbound 1, 4336w)_
- `/crypto-stablecoin-license-thailand/`  _(inbound 4, 3170w)_
- `/crypto-stablecoin-license-turkey/`  _(inbound 1, 3339w)_

### → 301 to /bermuda-crypto-license/  (4 pages)
- `/crypto-exchange-license-bermuda/`  _(inbound 14, 3092w)_
- `/crypto-fund-license-bermuda/`  _(inbound 14, 4034w)_
- `/crypto-otc-desk-license-bermuda/`  _(inbound 13, 3326w)_
- `/crypto-wallet-custody-license-bermuda/`  _(inbound 13, 3418w)_

### → 301 to /marshall-islands-crypto-license/  (3 pages)
- `/crypto-gambling-license-marshall-islands/`  _(inbound 3, 3488w)_
- `/crypto-stablecoin-license-marshall-islands/`  _(inbound 3, 3558w)_
- `/crypto-token-issuance-license-marshall-islands/`  _(inbound 3, 3209w)_