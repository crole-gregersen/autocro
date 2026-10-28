# AutoCRO behaviour analysis — cycle1

Runs: R011  ·  Sessions: 3000  ·  Events: 24897

## 1. Headline KPIs

| Segment | Sessions | Bounce | Session ATC rate | Conversion | AOV | Revenue/visitor |
|---|---|---|---|---|---|---|
| all | 3000 | 28.7% | 6.5% | 2.6% | €143.89 | €3.79 |
| mobile | 1840 | 27.7% | 5.3% | 1.6% | €130.65 | €2.06 |
| desktop | 1160 | 30.3% | 8.4% | 4.3% | €151.57 | €6.53 |

## 2. Funnel (sessions reaching each step; step rate = vs previous step)

| Step | All | step rate | Mobile | step rate | Desktop | step rate | Mobile/Desktop step-rate ratio |
|---|---|---|---|---|---|---|---|
| session | 3000 | 100.0% | 1840 | 100.0% | 1160 | 100.0% | 1.00 |
| view_item | 1566 | 52.2% | 984 | 53.5% | 582 | 50.2% | 1.07 |
| add_to_cart | 195 | 12.5% | 97 | 9.9% | 98 | 16.8% | 0.59 |
| view_cart | 195 | 100.0% | 97 | 100.0% | 98 | 100.0% | 1.00 |
| begin_checkout | 97 | 49.7% | 34 | 35.1% | 63 | 64.3% | 0.55 |
| checkout_step1 | 89 | 91.8% | 32 | 94.1% | 57 | 90.5% | 1.04 |
| add_shipping_info | 84 | 94.4% | 30 | 93.8% | 54 | 94.7% | 0.99 |
| add_payment_info | 81 | 96.4% | 29 | 96.7% | 52 | 96.3% | 1.00 |
| purchase | 79 | 97.5% | 29 | 100.0% | 50 | 96.2% | 1.04 |

## 3. Product detail pages (view_item → add_to_cart, per PDP view)

| Cut | PDP views | ATCs | ATC/PDP view |
|---|---|---|---|
| cat = accessories | 783 | 74 | 9.5% |
| cat = backpacks | 725 | 56 | 7.7% |
| cat = footwear | 699 | 49 | 7.0% |
| cat = jackets | 715 | 60 | 8.4% |
| dev = desktop | 1078 | 126 | 11.7% |
| dev = mobile | 1844 | 113 | 6.1% |
| dev×cat = desktop/accessories | 302 | 38 | 12.6% |
| dev×cat = desktop/backpacks | 265 | 33 | 12.5% |
| dev×cat = desktop/footwear | 251 | 19 | 7.6% |
| dev×cat = desktop/jackets | 260 | 36 | 13.8% |
| dev×cat = mobile/accessories | 481 | 36 | 7.5% |
| dev×cat = mobile/backpacks | 460 | 23 | 5.0% |
| dev×cat = mobile/footwear | 448 | 30 | 6.7% |
| dev×cat = mobile/jackets | 455 | 24 | 5.3% |

| Device / price band | PDP views | ATCs | ATC rate |
|---|---|---|---|
| desktop <€100 | 615 | 73 | 11.9% |
| desktop >€150 | 192 | 27 | 14.1% |
| desktop €100–150 | 271 | 26 | 9.6% |
| mobile <€100 | 1041 | 61 | 5.9% |
| mobile >€150 | 349 | 21 | 6.0% |
| mobile €100–150 | 454 | 31 | 6.8% |

Size-validation errors (ATC clicked without size): mobile 5, desktop 11.

## 4. Cart & checkout

- Sessions viewing cart: 195; reaching checkout: 97 (49.7%).
- Checkouts with subtotal below free-shipping threshold (€100, i.e. paying €6.95 shipping): 40 (41.2%).
- Checkout → purchase, below €100 (pays shipping): 32/40 = 80.0%; add_payment_info → purchase: 100.0%
- Checkout → purchase, ≥ €100 (free shipping): 47/57 = 82.5%; add_payment_info → purchase: 95.9%
- Checkout step-1 completion type: {'checkout_contact': 89}
- Orders: 79; median order value €128.95; orders with subtotal €70–100 (just under threshold): 16 (20.3%)
- Items per order: 1.23

## 5. Landing pages

| Landing page type | Sessions | Bounce | Conversion |
|---|---|---|---|
| home | 1978 | 26.2% | 2.5% |
| plp | 585 | 33.2% | 3.1% |
| pdp | 234 | 45.3% | 3.0% |
| search | 203 | 21.2% | 2.5% |

## 6. Search

- Searches: 203; zero-result searches: 31 (15.3%). Top zero-result terms: {'tent': 31}

## Signals — largest absolute step losses (by device)

- mobile: 887 sessions lost entering `add_to_cart` (step rate 9.9%)
- mobile: 856 sessions lost entering `view_item` (step rate 53.5%)
- desktop: 578 sessions lost entering `view_item` (step rate 50.2%)
- desktop: 484 sessions lost entering `add_to_cart` (step rate 16.8%)
- mobile: 63 sessions lost entering `begin_checkout` (step rate 35.1%)
- desktop: 35 sessions lost entering `begin_checkout` (step rate 64.3%)
- desktop: 6 sessions lost entering `checkout_step1` (step rate 90.5%)
- desktop: 3 sessions lost entering `add_shipping_info` (step rate 94.7%)
