#!/usr/bin/env python3
"""Cycle step 1 (Analyse): KPIs from the event log vs public benchmarks.
Usage: python3 analysis/benchmark.py --runs R011 --label cycle1  ->  reports/benchmark-<label>.json/.md
Engaged session proxy: >=2 page views or an add-to-cart (bots have no reliable time-on-site)."""
import argparse, json, os
from collections import Counter, defaultdict
from common import ROOT, load_events, build_sessions

ap = argparse.ArgumentParser(); ap.add_argument("--runs", required=True); ap.add_argument("--label", default="latest"); a = ap.parse_args()
B = json.load(open(os.path.join(ROOT, "config/benchmarks.json")))
evs = load_events(set(a.runs.split(",")))
S = build_sessions(evs)
for s in S:
    s["n"] = Counter(e["event"] for e in s["events"])
    s["units"] = sum(i.get("quantity", 1) for e in s["events"] if e["event"] == "purchase" for i in e.get("items", []))
    s["engaged"] = len(s["page_types"]) >= 2 or s["n"]["add_to_cart"] > 0


def kpis(ss):
    E = [s for s in ss if s["engaged"]]; n = len(E) or 1
    tx = sum(s["n"]["purchase"] for s in E); atc_s = sum(1 for s in E if s["n"]["add_to_cart"]); bc = sum(1 for s in E if s["n"]["begin_checkout"])
    rev = sum(s["revenue"] for s in E)
    return dict(sessions=len(ss), engaged=len(E), cvr=tx / n, atc_rate=sum(s["n"]["add_to_cart"] for s in E) / n,
                selection=sum(1 for s in E if s["n"]["view_item"]) / n, cart_commit=bc / atc_s if atc_s else 0,
                checkout_conv=tx / bc if bc else 0, cart_abandon=1 - tx / atc_s if atc_s else 0,
                units=sum(s["units"] for s in E) / tx if tx else 0, aov=rev / tx if tx else 0, arpu=rev / n, transactions=tx)


R = {"all": kpis(S), "mobile": kpis([s for s in S if s["device"] == "mobile"]), "desktop": kpis([s for s in S if s["device"] == "desktop"])}
R["all"]["mob_desk_ratio"] = R["mobile"]["cvr"] / R["desktop"]["cvr"] if R["desktop"]["cvr"] else 0
# extra diagnostics for hypothesis work
diag = {}
srch = [e for s in S for e in s["events"] if e["event"] == "view_search_results"]
diag["search_zero_share"] = sum(1 for e in srch if not e.get("results")) / len(srch) if srch else 0
diag["zero_terms"] = Counter(e["search_term"] for e in srch if not e.get("results")).most_common(5)
orders = [e for s in S for e in s["events"] if e["event"] == "purchase"]
diag["orders_below_free_ship"] = sum(1 for o in orders if o["value"] - o.get("shipping", 0) < 100) / len(orders) if orders else 0
diag["orders_70_100"] = sum(1 for o in orders if 70 <= o["value"] - o.get("shipping", 0) < 100) / len(orders) if orders else 0
mc = Counter(e.get("trigger") for s in S for e in s["events"] if e["event"] == "view_minicart")
diag["minicart_opens"] = dict(mc)
pdp_views = Counter(); pdp_atc = Counter()
for s in S:
    last = None
    for e in s["events"]:
        if e["event"] == "view_item": last = e["items"][0]; pdp_views[(s["device"], last["item_category"])] += 1
        elif e["event"] == "add_to_cart" and last and "/p/" in e.get("page_location", ""): pdp_atc[(s["device"], last["item_category"])] += 1
diag["pdp_atc_by_device_cat"] = {f"{d}/{c}": round(pdp_atc[(d, c)] / v, 4) for (d, c), v in sorted(pdp_views.items())}
diag["sale_vs_full_pdp_atc"] = None
sale_ids = {p["id"] for p in json.load(open(os.path.join(ROOT, "site/data/products.json")))["products"] if p.get("sale_price")}
sv = sum(1 for s in S for e in s["events"] if e["event"] == "view_item" and e["items"][0]["item_id"] in sale_ids)
sa = sum(1 for s in S for e in s["events"] if e["event"] == "add_to_cart" and e["items"][0]["item_id"] in sale_ids)
fv = sum(1 for s in S for e in s["events"] if e["event"] == "view_item" and e["items"][0]["item_id"] not in sale_ids)
fa = sum(1 for s in S for e in s["events"] if e["event"] == "add_to_cart" and e["items"][0]["item_id"] not in sale_ids)
diag["sale_vs_full_pdp_atc"] = {"sale": round(sa / sv, 4) if sv else 0, "full_price": round(fa / fv, 4) if fv else 0}
lp = defaultdict(list)
for s in S:
    if s["engaged"]: lp[s["landing"]].append(s)
diag["landing_cvr"] = {k: round(sum(x["n"]["purchase"] > 0 for x in v) / len(v), 4) for k, v in lp.items()}


def status(key, v):
    m = B["metrics"][key]
    if m.get("lower_is_better"):
        return "top" if v <= m["top"] else "good" if v <= m["good"] else "ok" if v <= m["low"] else "below"
    return "top" if v >= m["top"] else "good" if v >= m["good"] else "ok" if v >= m["low"] else "below"


rows = []
for key, m in B["metrics"].items():
    v = R["all"].get(key)
    rows.append(dict(key=key, label=m["label"], def_=m["def"], value=v, mobile=R["mobile"].get(key), desktop=R["desktop"].get(key), status=status(key, v), bench=m))
out = dict(label=a.label, runs=a.runs, kpis=R, rows=rows, diag=diag, sources=B["sources"])
os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "reports", f"benchmark-{a.label}.json"), "w"), indent=1, default=str)
fmt = lambda k, v: f"{v:.2f}" if k in ("units",) else f"{v:.0%}" if k in ("mob_desk_ratio",) else f"{v:.1%}"
md = [f"# Step 1 · Analysis vs benchmarks — {a.label}", f"Runs: {a.runs} · sessions {R['all']['sessions']} · engaged {R['all']['engaged']}", "",
      "| Metric | Fjeldspor | Mobile | Desktop | Benchmark | Status |", "|---|---|---|---|---|---|"]
for r in rows:
    md.append(f"| {r['label']} | {fmt(r['key'], r['value'])} | {fmt(r['key'], r['mobile']) if r['mobile'] is not None else ''} | {fmt(r['key'], r['desktop']) if r['desktop'] is not None else ''} | {r['bench']['note']} | {r['status']} |")
md += ["", "## Diagnostics", "```", json.dumps(diag, indent=1, default=str), "```"]
open(os.path.join(ROOT, "reports", f"benchmark-{a.label}.md"), "w").write("\n".join(md) + "\n")
print("\n".join(md[:14]))
