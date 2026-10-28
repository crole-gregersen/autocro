#!/usr/bin/env python3
"""SEALED (operator-side): compare a local simulator run with realistic e-commerce ranges.
Ranges are rounded, anonymised benchmarks from a real D2C webshop (not published per client)."""
import json, sys, gzip, os
from collections import defaultdict
TARGET = {"cvr": (0.025, 0.045), "atc_rate": (0.06, 0.11), "selection": (0.62, 0.76), "cart_commit_mob": (0.38, 0.52),
          "cart_commit_desk": (0.58, 0.75), "checkout_conv": (0.65, 0.90), "cart_abandon": (0.52, 0.65), "desk_mob_cvr_ratio": (1.8, 3.0), "units": (1.3, 2.2)}
f = sys.argv[1]
op = gzip.open if f.endswith('.gz') else open
S = defaultdict(lambda: {"ev": defaultdict(int), "dev": None, "pv": 0, "units": 0})
for l in op(f, 'rt'):
    e = json.loads(l); s = S[e["session_id"]]; s["dev"] = e["device_category"]; s["ev"][e["event"]] += 1
    if e["event"] == "page_view": s["pv"] += 1
    if e["event"] == "purchase": s["units"] += sum(i.get("quantity", 1) for i in e.get("items", []))
def m(ss):
    eng = [s for s in ss if s["pv"] >= 2 or s["ev"]["add_to_cart"]]
    n = len(eng) or 1; tx = sum(s["ev"]["purchase"] for s in eng); atc = sum(s["ev"]["add_to_cart"] for s in eng)
    vi = sum(1 for s in eng if s["ev"]["view_item"]); bc = sum(1 for s in eng if s["ev"]["begin_checkout"]); atcs = sum(1 for s in eng if s["ev"]["add_to_cart"])
    return dict(engaged=len(eng), engaged_share=len(eng) / max(len(ss), 1), cvr=tx / n, atc_rate=atc / n, selection=vi / n,
                cart_commit=bc / atcs if atcs else 0, checkout_conv=tx / bc if bc else 0, cart_abandon=1 - tx / atcs if atcs else 0,
                units=sum(s["units"] for s in eng) / tx if tx else 0)
A = m(list(S.values())); M = m([s for s in S.values() if s["dev"] == "mobile"]); D = m([s for s in S.values() if s["dev"] == "desktop"])
vals = {"cvr": A["cvr"], "atc_rate": A["atc_rate"], "selection": A["selection"], "cart_commit_mob": M["cart_commit"], "cart_commit_desk": D["cart_commit"],
        "checkout_conv": A["checkout_conv"], "cart_abandon": A["cart_abandon"], "desk_mob_cvr_ratio": D["cvr"] / M["cvr"] if M["cvr"] else 0, "units": A["units"]}
print(f"sessions {len(S)} · engaged {A['engaged']} ({A['engaged_share']:.0%}) · CVR mob {M['cvr']:.2%} desk {D['cvr']:.2%}")
for k, v in vals.items():
    lo, hi = TARGET[k]; ok = lo <= v <= hi
    print(f"  {'OK ' if ok else 'OFF'} {k:20} {v:8.3f}   target {lo}–{hi}")
