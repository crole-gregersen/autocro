# AutoCRO behaviour analysis — baseline

Runs: R001, R002  ·  Sessions: 3000  ·  Events: 28944

## 1. Headline KPIs

| Segment | Sessions | Bounce | Session ATC rate | Conversion | AOV | Revenue/visitor |
|---|---|---|---|---|---|---|
| all | 3000 | 25.4% | 15.8% | 6.1% | €124.17 | €7.62 |
| mobile | 1892 | 27.3% | 13.1% | 5.0% | €127.10 | €6.38 |
| desktop | 1108 | 22.1% | 20.3% | 8.0% | €121.05 | €9.72 |

## 2. Funnel (sessions reaching each step; step rate = vs previous step)

| Step | All | step rate | Mobile | step rate | Desktop | step rate | Mobile/Desktop step-rate ratio |
|---|---|---|---|---|---|---|---|
| session | 3000 | 100.0% | 1892 | 100.0% | 1108 | 100.0% | 1.00 |
| view_item | 2358 | 78.6% | 1446 | 76.4% | 912 | 82.3% | 0.93 |
| add_to_cart | 473 | 20.1% | 248 | 17.2% | 225 | 24.7% | 0.70 |
| view_cart | 473 | 100.0% | 248 | 100.0% | 225 | 100.0% | 1.00 |
| begin_checkout | 360 | 76.1% | 185 | 74.6% | 175 | 77.8% | 0.96 |
| checkout_step1 | 248 | 68.9% | 123 | 66.5% | 125 | 71.4% | 0.93 |
| add_shipping_info | 228 | 91.9% | 115 | 93.5% | 113 | 90.4% | 1.03 |
| add_payment_info | 217 | 95.2% | 110 | 95.7% | 107 | 94.7% | 1.01 |
| purchase | 184 | 84.8% | 95 | 86.4% | 89 | 83.2% | 1.04 |

## 3. Product detail pages (view_item → add_to_cart, per PDP view)

| Cut | PDP views | ATCs | ATC/PDP view |
|---|---|---|---|
| cat = accessories | 1067 | 128 | 12.0% |
| cat = backpacks | 972 | 120 | 12.3% |
| cat = footwear | 921 | 113 | 12.3% |
| cat = jackets | 981 | 135 | 13.8% |
| dev = desktop | 1505 | 239 | 15.9% |
| dev = mobile | 2436 | 257 | 10.6% |
| dev×cat = desktop/accessories | 402 | 69 | 17.2% |
| dev×cat = desktop/backpacks | 399 | 57 | 14.3% |
| dev×cat = desktop/footwear | 350 | 48 | 13.7% |
| dev×cat = desktop/jackets | 354 | 65 | 18.4% |
| dev×cat = mobile/accessories | 665 | 59 | 8.9% |
| dev×cat = mobile/backpacks | 573 | 63 | 11.0% |
| dev×cat = mobile/footwear | 571 | 65 | 11.4% |
| dev×cat = mobile/jackets | 627 | 70 | 11.2% |

| Device / price band | PDP views | ATCs | ATC rate |
|---|---|---|---|
| desktop <€100 | 751 | 115 | 15.3% |
| desktop >€150 | 319 | 52 | 16.3% |
| desktop €100–150 | 435 | 72 | 16.6% |
| mobile <€100 | 1229 | 116 | 9.4% |
| mobile >€150 | 518 | 56 | 10.8% |
| mobile €100–150 | 689 | 85 | 12.3% |

Size-validation errors (ATC clicked without size): mobile 20, desktop 16.

## 4. Cart & checkout

- Sessions viewing cart: 473; reaching checkout: 360 (76.1%).
- Checkouts with subtotal below free-shipping threshold (€100, i.e. paying €6.95 shipping): 166 (46.1%).
- Checkout → purchase, below €100 (pays shipping): 78/166 = 47.0%; add_payment_info → purchase: 73.6%
- Checkout → purchase, ≥ €100 (free shipping): 106/194 = 54.6%; add_payment_info → purchase: 95.5%
- Checkout step-1 completion type: {'sign_up': 248}
- Orders: 184; median order value €107.95; orders with subtotal €70–100 (just under threshold): 30 (16.3%)
- Items per order: 1.05

## 5. Landing pages

| Landing page type | Sessions | Bounce | Conversion |
|---|---|---|---|
| home | 1973 | 23.1% | 6.0% |
| plp | 596 | 24.0% | 6.2% |
| pdp | 232 | 51.7% | 6.5% |
| search | 199 | 21.6% | 7.0% |

## 6. Search

- Searches: 199; zero-result searches: 24 (12.1%). Top zero-result terms: {'tent': 24}

## Signals — largest absolute step losses (by device)

- mobile: 1198 sessions lost entering `add_to_cart` (step rate 17.2%)
- desktop: 687 sessions lost entering `add_to_cart` (step rate 24.7%)
- mobile: 446 sessions lost entering `view_item` (step rate 76.4%)
- desktop: 196 sessions lost entering `view_item` (step rate 82.3%)
- mobile: 63 sessions lost entering `begin_checkout` (step rate 74.6%)
- mobile: 62 sessions lost entering `checkout_step1` (step rate 66.5%)
- desktop: 50 sessions lost entering `checkout_step1` (step rate 71.4%)
- desktop: 50 sessions lost entering `begin_checkout` (step rate 77.8%)
