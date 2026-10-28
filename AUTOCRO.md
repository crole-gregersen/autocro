# AutoCRO — operating manual (read this first, every session)

AutoCRO is a proof of concept for a **self-optimising website**, built and operated by Claude for CROle (IMPACT Commerce).
A fictional webshop, **Fjeldspor**, is tracked with GA4-shaped ecommerce events. Claude analyses behaviour, writes
hypotheses, builds A/B test variants, runs them on simulated traffic, and ships or kills them by fixed rules.

## Repository map
| Path | What |
|---|---|
| `site/` | The shop (static SPA). `js/app.js` renders from feature flags; `js/tracking.js` = GA4/dataLayer events; `js/experiments.js` = A/B engine |
| `site/config/site-config.json` | **Shipped state**: feature flags (+ `device_features` for device-targeted winners) + CSS + changelog. GA4 Measurement ID goes here |
| `site/config/experiments.json` | Experiment registry (running / shipped / stopped / invalid) |
| `config/decision-rules.json` | Ship/kill rules R1–R7 |
| `sim/run.js`, `sim/perceive.js` | Simulated shoppers. They react only to what is rendered (text, visibility, above-the-fold) |
| `sim/sealed/` | **SEALED ground truth** (persona model + truth logs). The analyst/ideation side must NEVER open these files |
| `analysis/analyze.py` | Behaviour report → `reports/analysis-<label>.md` |
| `analysis/evaluate.py` | Experiment stats + decisions (`--apply` ships/kills and logs) |
| `data/events/*.jsonl` | Event log (one file per traffic run). Same events also go to GA4 when configured |
| `docs/decision-log.md`, `docs/hypothesis-backlog.md` | Decisions and hypotheses |

## The blinding rule
Claude plays two roles. As **operator of the simulator** it may run `sim/run.js`. As **CRO analyst** it may only use
`data/events`, `reports/`, GA4 and the rendered site. Never read `sim/sealed/*` when forming hypotheses — that would
be cheating and would invalidate the POC. Only `sim/sealed/score.py` (end-of-POC scoring, run on CROle's request) may.

## One optimisation cycle
1. **Traffic**: serve the site (`python3 -m http.server 8787 -d site`) and run
   `node sim/run.js --sessions <n> --concurrency 14 --seed <unique> --run R<next>` (≈ 5–6 sessions/s).
2. **Evaluate** running experiments: `python3 analysis/evaluate.py --apply`. Shipped variants are merged into site-config.
3. **Analyse**: `python3 analysis/analyze.py --label <cycle>` (use runs since the last ship for a clean baseline).
4. **Ideate**: from the report, add/refresh hypotheses in `docs/hypothesis-backlog.md`
   (format: observation → hypothesis → change → primary metric → expected effect → PIE/ICE score).
5. **Build**: for the top hypothesis, add a variant to `experiments.json`. Prefer existing feature flags; if none fits,
   implement a new flag in `site/js/app.js` (default = current behaviour) and use it. Keep all `data-ac` hooks.
   Respect R6 (no overlapping features/pages; ≤3 concurrent).
6. **Deploy**: commit + push (GitHub Pages) once hosting is connected.
7. Repeat. Report to CROle: what was learned, shipped, killed, what's next.

## Experiment schema
```json
{"id":"EXP001","name":"…","status":"running","created":"YYYY-MM-DD",
 "hypothesis":"Because we saw X, we believe Y will Z, measured by M",
 "exposure_route":"p",            // fire impression on first visit to route: '', 'home', 'c', 'p', 'cart', 'checkout'
 "targeting":{"device":"all"},    // all | mobile | desktop
 "traffic_allocation":100,
 "primary_metric":"purchase", "secondary_metrics":["add_to_cart"], "guardrails":["rpv"],
 "variants":[{"id":"control","weight":50,"features":{}},
             {"id":"B","weight":50,"features":{"flag":"value"},"css":""}]}
```

## Status log
- 2026-10-28 · Cycle 1: baseline 3,000 sessions (CR 6.1%). EXP001 guest checkout (+44% purchase), EXP002 cart shipping info (+22%), EXP003 mobile compact gallery (+53% mobile ATC) all SHIPPED. Post-cycle run CR 10.3% (EXP001 still at 50% in that run).
- Next: fresh baseline run on the new control, re-analyse, then backlog #4–#6 (PDP shipping note, free-shipping progress bar, PDP social proof).
- Not yet online: needs GitHub repo + token (hosting/persistence) and GA4 Measurement ID.
