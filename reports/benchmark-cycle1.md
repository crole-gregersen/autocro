# Step 1 · Analysis vs benchmarks — cycle1
Runs: R011 · sessions 3000 · engaged 2139

| Metric | Fjeldspor | Mobile | Desktop | Benchmark | Status |
|---|---|---|---|---|---|
| Conversion rate | 3.7% | 2.2% | 6.2% | DY global 2.66%; top 20% >3.2%; top 10% 4.7%+; Fashion & Apparel 1.4–2.9% | good |
| Add-to-cart rate | 11.2% | 8.5% | 15.6% | Global ~6%; top Shopify stores 7.5–9.6%; DY industry range 3.2–11.1% | top |
| Selection index | 68.3% | 68.8% | 67.3% | No public benchmark; typical healthy range used by CRO teams | good |
| Checkout conversion | 81.4% | 85.3% | 79.4% | Average 45%; top 20% 59%; top 10% 66% | top |
| Cart abandonment | 59.5% | 70.1% | 49.0% | Typical 70–78%; best DY industry 56.6% | good |
| Units per transaction | 1.24 | 1.10 | 1.32 | DY: Fashion, Accessories & Apparel 2.91 (lowest industry) | below |
| Mobile ÷ desktop conversion | 35% |  |  | Videowise: desktop ~3.0% vs mobile ~2.8%; older Adobe data: desktop ~3× smartphone | ok |

## Diagnostics
```
{
 "search_zero_share": 0.15270935960591134,
 "zero_terms": [
  [
   "tent",
   31
  ]
 ],
 "orders_below_free_ship": 0.4050632911392405,
 "orders_70_100": 0.20253164556962025,
 "minicart_opens": {
  "add_to_cart": 239
 },
 "pdp_atc_by_device_cat": {
  "desktop/accessories": 0.1258,
  "desktop/backpacks": 0.1245,
  "desktop/footwear": 0.0757,
  "desktop/jackets": 0.1385,
  "mobile/accessories": 0.0748,
  "mobile/backpacks": 0.05,
  "mobile/footwear": 0.067,
  "mobile/jackets": 0.0527
 },
 "sale_vs_full_pdp_atc": {
  "sale": 0.0865,
  "full_price": 0.0806
 },
 "landing_cvr": {
  "home": 0.0336,
  "plp": 0.046,
  "search": 0.0312,
  "pdp": 0.0547
 }
}
```
