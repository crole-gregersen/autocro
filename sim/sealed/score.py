#!/usr/bin/env python3
"""SEALED: scores AutoCRO against the hidden ground truth. Run only on CROle's request.
Shows true conversion per run and which hidden frictions shoppers still encounter."""
import json, glob, os
from collections import defaultdict
D = os.path.dirname(os.path.abspath(__file__))
FRICTIONS = {
    "H1 mobile ATC below fold": lambda t: t["persona"]["device"] == "mobile" and t["seen"].get("pdpAtcAboveFold") is False,
    "H2 no social proof on PDP (sceptics)": lambda t: t["persona"]["sceptical"] and t["seen"].get("pdpSocialProof") is False,
    "H3 forced account at checkout": lambda t: t["seen"].get("accountRequired") is True,
    "H4 free-shipping threshold never seen": lambda t: "freeShippingThresholdSeen" in t["seen"] and not t["seen"]["freeShippingThresholdSeen"],
    "H5 popup blocking landing": lambda t: t["seen"].get("overlayOnLanding") is True,
    "H6 shipping-cost surprise at checkout": lambda t: (t["seen"].get("checkoutShipping") or 0) > 0 and not t["seen"].get("shippingKnownCost"),
}
for f in sorted(glob.glob(os.path.join(D, "truth/*.jsonl*"))):
    import gzip; T = [json.loads(l) for l in (gzip.open(f, "rt") if f.endswith(".gz") else open(f))]
    n = len(T); cr = sum(t["outcome"]["purchased"] for t in T) / n
    err = sum(t["outcome"]["exit"] == "error" for t in T)
    hit = {k: sum(1 for t in T if "seen" in t and fn(t)) for k, fn in FRICTIONS.items()}
    print(f"{os.path.basename(f).split(".")[0]}: n={n} true CR={100*cr:.2f}% errors={err}  frictions hit: " + ", ".join(f"{k.split()[0]}={v}" for k, v in hit.items()))
