#!/usr/bin/env python3
"""AutoCRO behaviour analysis -> reports/analysis-<label>.md (+ .json)
Usage: python3 analysis/analyze.py --runs R001,R002 --label baseline [--exclude-exposed]
"""
import argparse, json, os
from collections import defaultdict, Counter
from common import ROOT, FUNNEL, load_events, build_sessions

ap = argparse.ArgumentParser()
ap.add_argument("--runs", default="")
ap.add_argument("--label", default="latest")
ap.add_argument("--exclude-exposed", action="store_true", help="only sessions not in any experiment variant other than control")
a = ap.parse_args()
runs = set(filter(None, a.runs.split(",")))
evs = load_events(runs or None)
S = build_sessions(evs)
if a.exclude_exposed:
    S = [s for s in S if all(v == "control" for v in s["exposures"].values())]

pct = lambda x: f"{100 * x:.1f}%"
eur = lambda x: f"€{x:,.2f}"
out = []; J = {}
w = out.append


def kpis(ss):
    n = len(ss) or 1
    orders = sum(s["orders"] for s in ss); rev = sum(s["revenue"] for s in ss)
    return dict(sessions=len(ss), bounce=sum(s["bounced"] for s in ss) / n,
                atc_rate=sum("add_to_cart" in s["steps"] for s in ss) / n,
                cr=sum(s["orders"] > 0 for s in ss) / n, orders=orders,
                aov=rev / orders if orders else 0, rpv=rev / n, revenue=rev)


segs = {"all": S, "mobile": [s for s in S if s["device"] == "mobile"], "desktop": [s for s in S if s["device"] == "desktop"]}
w(f"# AutoCRO behaviour analysis — {a.label}\n")
w(f"Runs: {', '.join(sorted({s['run'] for s in S}))}  ·  Sessions: {len(S)}  ·  Events: {len(evs)}\n")
w("## 1. Headline KPIs\n")
w("| Segment | Sessions | Bounce | Session ATC rate | Conversion | AOV | Revenue/visitor |")
w("|---|---|---|---|---|---|---|")
J["kpis"] = {}
for k, ss in segs.items():
    m = kpis(ss); J["kpis"][k] = m
    w(f"| {k} | {m['sessions']} | {pct(m['bounce'])} | {pct(m['atc_rate'])} | {pct(m['cr'])} | {eur(m['aov'])} | {eur(m['rpv'])} |")

w("\n## 2. Funnel (sessions reaching each step; step rate = vs previous step)\n")
w("| Step | All | step rate | Mobile | step rate | Desktop | step rate | Mobile/Desktop step-rate ratio |")
w("|---|---|---|---|---|---|---|---|")
J["funnel"] = {}
prev = {}
drops = []
for st in FUNNEL:
    row = [st]; rates = {}
    for k in ("all", "mobile", "desktop"):
        c = sum(st in s["steps"] for s in segs[k])
        r = c / prev[k] if prev.get(k) else 1.0
        rates[k] = r
        J["funnel"].setdefault(k, {})[st] = c
        if prev.get(k) and k != "all":
            drops.append((prev[k] - c, k, st, r))
        prev[k] = c
        row += [str(c), pct(r)]
    ratio = rates["mobile"] / rates["desktop"] if rates["desktop"] else 0
    row.append(f"{ratio:.2f}")
    w("| " + " | ".join(row) + " |")

w("\n## 3. Product detail pages (view_item → add_to_cart, per PDP view)\n")
pdp = defaultdict(lambda: [0, 0]); errs = Counter(); price_band = defaultdict(lambda: [0, 0])
band = lambda p: "<€100" if p < 100 else "€100–150" if p < 150 else ">€150"
for s in S:
    last = None
    for e in s["events"]:
        if e["event"] == "view_item":
            it = e["items"][0]; last = it
            for key in (("dev", s["device"]), ("cat", it["item_category"]), ("dev×cat", s["device"] + "/" + it["item_category"])):
                pdp[key][0] += 1
            price_band[(s["device"], band(it["price"]))][0] += 1
        elif e["event"] == "add_to_cart" and last and "/p/" in e["page_location"]:
            it = last
            for key in (("dev", s["device"]), ("cat", it["item_category"]), ("dev×cat", s["device"] + "/" + it["item_category"])):
                pdp[key][1] += 1
            price_band[(s["device"], band(it["price"]))][1] += 1
        elif e["event"] == "atc_error":
            errs[s["device"]] += 1
w("| Cut | PDP views | ATCs | ATC/PDP view |")
w("|---|---|---|---|")
J["pdp"] = {}
for key in sorted(pdp, key=lambda k: (k[0], k[1])):
    v, c = pdp[key]; J["pdp"]["/".join(key)] = [v, c]
    w(f"| {key[0]} = {key[1]} | {v} | {c} | {pct(c / v if v else 0)} |")
w("\n| Device / price band | PDP views | ATCs | ATC rate |\n|---|---|---|---|")
for key in sorted(price_band):
    v, c = price_band[key]
    w(f"| {key[0]} {key[1]} | {v} | {c} | {pct(c / v if v else 0)} |")
w(f"\nSize-validation errors (ATC clicked without size): mobile {errs['mobile']}, desktop {errs['desktop']}.")

w("\n## 4. Cart & checkout\n")
carts = [s for s in S if "view_cart" in s["steps"]]
bc = [s for s in S if "begin_checkout" in s["steps"]]
def subtotal_at(s, ev):
    for e in s["events"]:
        if e["event"] == ev:
            return e.get("value", 0)
below = [s for s in bc if (subtotal_at(s, "begin_checkout") or 0) < 100]
w(f"- Sessions viewing cart: {len(carts)}; reaching checkout: {len(bc)} ({pct(len(bc) / len(carts) if carts else 0)}).")
w(f"- Checkouts with subtotal below free-shipping threshold (€100, i.e. paying €6.95 shipping): {len(below)} ({pct(len(below) / len(bc) if bc else 0)}).")
for grp, name in ((below, "below €100 (pays shipping)"), ([s for s in bc if s not in below], "≥ €100 (free shipping)")):
    if grp:
        pay = sum("add_payment_info" in s["steps"] for s in grp); pur = sum("purchase" in s["steps"] for s in grp)
        w(f"- Checkout → purchase, {name}: {pur}/{len(grp)} = {pct(pur / len(grp))}; add_payment_info → purchase: {pct(pur / pay if pay else 0)}")
step1 = Counter(e["event"] for s in bc for e in s["events"] if e["event"] in ("sign_up", "checkout_contact"))
w(f"- Checkout step-1 completion type: {dict(step1)}")
orders = [e for s in S for e in s["events"] if e["event"] == "purchase"]
if orders:
    vals = sorted(o["value"] for o in orders)
    near = sum(1 for o in orders if 70 <= o["value"] - o.get("shipping", 0) < 100)
    w(f"- Orders: {len(orders)}; median order value {eur(vals[len(vals) // 2])}; orders with subtotal €70–100 (just under threshold): {near} ({pct(near / len(orders))})")
    w(f"- Items per order: {sum(len(o['items']) for o in orders) / len(orders):.2f}")

w("\n## 5. Landing pages\n")
w("| Landing page type | Sessions | Bounce | Conversion |\n|---|---|---|---|")
lp = defaultdict(list)
for s in S: lp[s["landing"]].append(s)
for k, ss in sorted(lp.items(), key=lambda x: -len(x[1])):
    m = kpis(ss); w(f"| {k} | {m['sessions']} | {pct(m['bounce'])} | {pct(m['cr'])} |")

w("\n## 6. Search\n")
srch = [e for s in S for e in s["events"] if e["event"] == "view_search_results"]
zero = Counter(e["search_term"] for e in srch if e.get("results", 0) == 0)
w(f"- Searches: {len(srch)}; zero-result searches: {sum(zero.values())} ({pct(sum(zero.values()) / len(srch) if srch else 0)}). Top zero-result terms: {dict(zero.most_common(5))}")

pop = Counter(e["event"] for s in S for e in s["events"] if e["event"] in ("popup_shown", "popup_closed", "newsletter_signup"))
if pop:
    w(f"\n## 7. Popups\n- {dict(pop)}")

w("\n## Signals — largest absolute step losses (by device)\n")
for lost, k, st, r in sorted(drops, reverse=True)[:8]:
    w(f"- {k}: {lost} sessions lost entering `{st}` (step rate {pct(r)})")

os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
p = os.path.join(ROOT, "reports", f"analysis-{a.label}.md")
open(p, "w").write("\n".join(out) + "\n")
json.dump(J, open(p[:-3] + ".json", "w"), indent=1, default=str)
print(p)
