# AutoCRO decision log

## 2026-10-28 · EXP002 Show shipping cost and free-shipping threshold in cart → **SHIP**

- Hypothesis: Because checkouts paying €6.95 shipping lose 26% at the final 'place order' step vs 4.5% for free-shipping orders, and shipping cost is first shown at checkout, we believe showing shipping cost and the €100 free-shipping threshold in the cart will reduce surprise abandonment and lift conversion, measured by purchase rate of cart visitors.
- R3 B beats control on purchase: +22.3% (p=0.0028, P(beat)=0.998); guardrails OK.
- Exposed: {'control': 447, 'B': 459}

## 2026-10-28 · EXP003 Mobile PDP: get Add to bag above the fold → **SHIP**

- Hypothesis: Because mobile PDP→add-to-cart is 10.6% vs 15.9% on desktop (ratio 0.67) across all categories and price bands, and on a 390px screen the tall 3-image gallery pushes 'Add to bag' below the fold, we believe making the button visible without scrolling will raise mobile add-to-cart rate.
- R3 B_compact_gallery beats control on add_to_cart: +53.4% (p=0.0000, P(beat)=1.000); guardrails OK.
- Exposed: {'control': 752, 'B_compact_gallery': 732, 'C_sticky_atc': 741}

## 2026-10-28 · EXP001 Guest checkout instead of forced account → **SHIP**

- Hypothesis: Because 31% of visitors who begin checkout drop at the mandatory account-creation step (step rate 68.9%, both devices), we believe letting customers check out as guest will raise checkout completion, measured by purchase rate of checkout visitors.
- R3 B beats control on purchase: +44.1% (p=0.0000, P(beat)=1.000); guardrails OK.
- Exposed: {'control': 495, 'B': 485}

