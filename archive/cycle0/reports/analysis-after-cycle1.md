# AutoCRO behaviour analysis — after-cycle1

Runs: R004  ·  Sessions: 2000  ·  Events: 20817

## 1. Headline KPIs

| Segment | Sessions | Bounce | Session ATC rate | Conversion | AOV | Revenue/visitor |
|---|---|---|---|---|---|---|
| all | 2000 | 25.6% | 20.8% | 10.3% | €115.19 | €11.92 |
| mobile | 1281 | 26.1% | 20.3% | 10.5% | €112.72 | €11.88 |
| desktop | 719 | 24.8% | 21.7% | 10.0% | €119.82 | €12.00 |

## 2. Funnel (sessions reaching each step; step rate = vs previous step)

| Step | All | step rate | Mobile | step rate | Desktop | step rate | Mobile/Desktop step-rate ratio |
|---|---|---|---|---|---|---|---|
| session | 2000 | 100.0% | 1281 | 100.0% | 719 | 100.0% | 1.00 |
| view_item | 1560 | 78.0% | 987 | 77.0% | 573 | 79.7% | 0.97 |
| add_to_cart | 416 | 26.7% | 260 | 26.3% | 156 | 27.2% | 0.97 |
| view_cart | 416 | 100.0% | 260 | 100.0% | 156 | 100.0% | 1.00 |
| begin_checkout | 305 | 73.3% | 193 | 74.2% | 112 | 71.8% | 1.03 |
| checkout_step1 | 234 | 76.7% | 149 | 77.2% | 85 | 75.9% | 1.02 |
| add_shipping_info | 222 | 94.9% | 142 | 95.3% | 80 | 94.1% | 1.01 |
| add_payment_info | 213 | 95.9% | 138 | 97.2% | 75 | 93.8% | 1.04 |
| purchase | 207 | 97.2% | 135 | 97.8% | 72 | 96.0% | 1.02 |

## 3. Product detail pages (view_item → add_to_cart, per PDP view)

| Cut | PDP views | ATCs | ATC/PDP view |
|---|---|---|---|
| cat = accessories | 798 | 170 | 21.3% |
| cat = backpacks | 683 | 109 | 16.0% |
| cat = footwear | 593 | 95 | 16.0% |
| cat = jackets | 600 | 100 | 16.7% |
| dev = desktop | 990 | 180 | 18.2% |
| dev = mobile | 1684 | 294 | 17.5% |
| dev×cat = desktop/accessories | 307 | 60 | 19.5% |
| dev×cat = desktop/backpacks | 252 | 46 | 18.3% |
| dev×cat = desktop/footwear | 197 | 34 | 17.3% |
| dev×cat = desktop/jackets | 234 | 40 | 17.1% |
| dev×cat = mobile/accessories | 491 | 110 | 22.4% |
| dev×cat = mobile/backpacks | 431 | 63 | 14.6% |
| dev×cat = mobile/footwear | 396 | 61 | 15.4% |
| dev×cat = mobile/jackets | 366 | 60 | 16.4% |

| Device / price band | PDP views | ATCs | ATC rate |
|---|---|---|---|
| desktop <€100 | 519 | 99 | 19.1% |
| desktop >€150 | 187 | 29 | 15.5% |
| desktop €100–150 | 284 | 52 | 18.3% |
| mobile <€100 | 890 | 167 | 18.8% |
| mobile >€150 | 343 | 49 | 14.3% |
| mobile €100–150 | 451 | 78 | 17.3% |

Size-validation errors (ATC clicked without size): mobile 9, desktop 11.

## 4. Cart & checkout

- Sessions viewing cart: 416; reaching checkout: 305 (73.3%).
- Checkouts with subtotal below free-shipping threshold (€100, i.e. paying €6.95 shipping): 138 (45.2%).
- Checkout → purchase, below €100 (pays shipping): 99/138 = 71.7%; add_payment_info → purchase: 97.1%
- Checkout → purchase, ≥ €100 (free shipping): 108/167 = 64.7%; add_payment_info → purchase: 97.3%
- Checkout step-1 completion type: {'checkout_contact': 139, 'sign_up': 95}
- Orders: 207; median order value €107.95; orders with subtotal €70–100 (just under threshold): 34 (16.4%)
- Items per order: 1.14

## 5. Landing pages

| Landing page type | Sessions | Bounce | Conversion |
|---|---|---|---|
| home | 1316 | 23.4% | 10.6% |
| plp | 398 | 22.9% | 9.5% |
| pdp | 144 | 50.0% | 12.5% |
| search | 142 | 28.9% | 8.5% |

## 6. Search

- Searches: 142; zero-result searches: 15 (10.6%). Top zero-result terms: {'tent': 15}

## Signals — largest absolute step losses (by device)

- mobile: 727 sessions lost entering `add_to_cart` (step rate 26.3%)
- desktop: 417 sessions lost entering `add_to_cart` (step rate 27.2%)
- mobile: 294 sessions lost entering `view_item` (step rate 77.0%)
- desktop: 146 sessions lost entering `view_item` (step rate 79.7%)
- mobile: 67 sessions lost entering `begin_checkout` (step rate 74.2%)
- mobile: 44 sessions lost entering `checkout_step1` (step rate 77.2%)
- desktop: 44 sessions lost entering `begin_checkout` (step rate 71.8%)
- desktop: 27 sessions lost entering `checkout_step1` (step rate 75.9%)
