# AutoCRO behaviour analysis — cycle2-baseline

Runs: R005  ·  Sessions: 3000  ·  Events: 31038

## 1. Headline KPIs

| Segment | Sessions | Bounce | Session ATC rate | Conversion | AOV | Revenue/visitor |
|---|---|---|---|---|---|---|
| all | 3000 | 25.5% | 21.2% | 12.8% | €123.15 | €15.72 |
| mobile | 1861 | 25.3% | 21.2% | 12.4% | €122.09 | €15.09 |
| desktop | 1139 | 26.0% | 21.3% | 13.4% | €124.75 | €16.76 |

## 2. Funnel (sessions reaching each step; step rate = vs previous step)

| Step | All | step rate | Mobile | step rate | Desktop | step rate | Mobile/Desktop step-rate ratio |
|---|---|---|---|---|---|---|---|
| session | 3000 | 100.0% | 1861 | 100.0% | 1139 | 100.0% | 1.00 |
| view_item | 2367 | 78.9% | 1482 | 79.6% | 885 | 77.7% | 1.02 |
| add_to_cart | 637 | 26.9% | 394 | 26.6% | 243 | 27.5% | 0.97 |
| view_cart | 637 | 100.0% | 394 | 100.0% | 243 | 100.0% | 1.00 |
| begin_checkout | 479 | 75.2% | 287 | 72.8% | 192 | 79.0% | 0.92 |
| checkout_step1 | 447 | 93.3% | 270 | 94.1% | 177 | 92.2% | 1.02 |
| add_shipping_info | 419 | 93.7% | 253 | 93.7% | 166 | 93.8% | 1.00 |
| add_payment_info | 395 | 94.3% | 238 | 94.1% | 157 | 94.6% | 0.99 |
| purchase | 383 | 97.0% | 230 | 96.6% | 153 | 97.5% | 0.99 |

## 3. Product detail pages (view_item → add_to_cart, per PDP view)

| Cut | PDP views | ATCs | ATC/PDP view |
|---|---|---|---|
| cat = accessories | 1133 | 245 | 21.6% |
| cat = backpacks | 1000 | 157 | 15.7% |
| cat = footwear | 912 | 145 | 15.9% |
| cat = jackets | 945 | 162 | 17.1% |
| dev = desktop | 1512 | 271 | 17.9% |
| dev = mobile | 2478 | 438 | 17.7% |
| dev×cat = desktop/accessories | 404 | 94 | 23.3% |
| dev×cat = desktop/backpacks | 379 | 61 | 16.1% |
| dev×cat = desktop/footwear | 352 | 53 | 15.1% |
| dev×cat = desktop/jackets | 377 | 63 | 16.7% |
| dev×cat = mobile/accessories | 729 | 151 | 20.7% |
| dev×cat = mobile/backpacks | 621 | 96 | 15.5% |
| dev×cat = mobile/footwear | 560 | 92 | 16.4% |
| dev×cat = mobile/jackets | 568 | 99 | 17.4% |

| Device / price band | PDP views | ATCs | ATC rate |
|---|---|---|---|
| desktop <€100 | 769 | 149 | 19.4% |
| desktop >€150 | 329 | 55 | 16.7% |
| desktop €100–150 | 414 | 67 | 16.2% |
| mobile <€100 | 1285 | 239 | 18.6% |
| mobile >€150 | 480 | 82 | 17.1% |
| mobile €100–150 | 713 | 117 | 16.4% |

Size-validation errors (ATC clicked without size): mobile 23, desktop 14.

## 4. Cart & checkout

- Sessions viewing cart: 637; reaching checkout: 479 (75.2%).
- Checkouts with subtotal below free-shipping threshold (€100, i.e. paying €6.95 shipping): 191 (39.9%).
- Checkout → purchase, below €100 (pays shipping): 151/191 = 79.1%; add_payment_info → purchase: 97.4%
- Checkout → purchase, ≥ €100 (free shipping): 232/288 = 80.6%; add_payment_info → purchase: 96.7%
- Checkout step-1 completion type: {'checkout_contact': 447}
- Orders: 383; median order value €112.95; orders with subtotal €70–100 (just under threshold): 53 (13.8%)
- Items per order: 1.10

## 5. Landing pages

| Landing page type | Sessions | Bounce | Conversion |
|---|---|---|---|
| home | 2000 | 23.7% | 12.3% |
| plp | 605 | 20.7% | 14.0% |
| pdp | 232 | 57.3% | 12.5% |
| search | 163 | 20.9% | 13.5% |

## 6. Search

- Searches: 163; zero-result searches: 17 (10.4%). Top zero-result terms: {'tent': 17}

## Signals — largest absolute step losses (by device)

- mobile: 1088 sessions lost entering `add_to_cart` (step rate 26.6%)
- desktop: 642 sessions lost entering `add_to_cart` (step rate 27.5%)
- mobile: 379 sessions lost entering `view_item` (step rate 79.6%)
- desktop: 254 sessions lost entering `view_item` (step rate 77.7%)
- mobile: 107 sessions lost entering `begin_checkout` (step rate 72.8%)
- desktop: 51 sessions lost entering `begin_checkout` (step rate 79.0%)
- mobile: 17 sessions lost entering `checkout_step1` (step rate 94.1%)
- mobile: 17 sessions lost entering `add_shipping_info` (step rate 93.7%)
