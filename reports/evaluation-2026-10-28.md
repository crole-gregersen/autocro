# Experiment evaluation — 2026-10-28

### EXP001 — Guest checkout instead of forced account
Exposed visitors: {'control': 495, 'B': 485} · SRM p=0.745

| Variant | Metric | Control | Variant | Rel. uplift | 95% CI (rel) | p | P(beat) |
|---|---|---|---|---|---|---|---|
| B | purchase | 54.95% | 79.18% | +44.1% | +33.7% … +54.4% | 0.0000 | 1.000 |
| B | checkout_step1 | 66.26% | 92.58% | +39.7% | +32.5% … +46.9% | 0.0000 | 1.000 |
| B | rpv | €61.89 | €91.47 | +47.8% | | 0.0000 | |
| B | aov | €112.64 | €115.53 | +2.6% | | 0.5738 | |

**Decision: SHIP** — R3 B beats control on purchase: +44.1% (p=0.0000, P(beat)=1.000); guardrails OK.

