# Hypothesis backlog

Scored ICE (Impact, Confidence, Ease; 1–10). Source: reports/analysis-baseline.md (3,000 sessions, runs R001–R002).

| # | Observation | Hypothesis / change | Primary metric | ICE | Status |
|---|---|---|---|---|---|
| 1 | Checkout step 1 (forced account) step rate 68.9% vs 92–95% for later steps | Allow guest checkout | purchase (checkout visitors) | 9·9·9 = 729 | EXP001 running |
| 2 | Final step completion 73.6% when paying shipping vs 95.5% when free; cost first shown at checkout | Show shipping cost + €100 threshold in cart | purchase (cart visitors) | 8·8·9 = 576 | EXP002 running |
| 3 | Mobile PDP→ATC 10.6% vs desktop 15.9%, consistent across categories/prices | ATC above fold on mobile (compact gallery / sticky ATC) | add_to_cart (mobile PDP) | 8·7·8 = 448 | EXP003 running |
| 4 | Same as #2, but earlier in journey | Shipping/threshold note on PDP (after EXP003 concludes — same page) | purchase | 6·6·9 = 324 | queued |
| 5 | 1.05 items/order; 16% of orders €70–100 (just under threshold) | Free-shipping progress bar sitewide | rpv / AOV | 6·5·8 = 240 | queued (after EXP002) |
| 6 | PDP-landing sessions bounce 51.7% | Add social proof / reviews on PDP | add_to_cart | 5·4·9 = 180 | queued |
| 7 | 12% of searches return zero results (all "tent") | Zero-result page with category suggestions | view_item from search | 2·6·7 = 84 | backlog |
