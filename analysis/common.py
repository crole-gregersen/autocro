"""Shared loading + session building for AutoCRO analysis. Reads ONLY data/events (never sim/sealed)."""
import json, glob, os, math, random, gzip
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FUNNEL = ["session", "view_item", "add_to_cart", "view_cart", "begin_checkout",
          "checkout_step1", "add_shipping_info", "add_payment_info", "purchase"]


def load_events(runs=None):
    files = sorted(glob.glob(os.path.join(ROOT, "data/events/*.jsonl")) + glob.glob(os.path.join(ROOT, "data/events/*.jsonl.gz")))
    evs = []
    for f in files:
        run = os.path.basename(f).split(".")[0]
        if run.startswith("TEST"):
            continue
        if runs and run not in runs:
            continue
        with (gzip.open(f, "rt") if f.endswith(".gz") else open(f)) as fh:
            for line in fh:
                if line.strip():
                    evs.append(json.loads(line))
    return evs


def build_sessions(evs):
    S = {}
    for e in sorted(evs, key=lambda e: e["ts"]):
        sid = e["session_id"]
        s = S.get(sid)
        if s is None:
            s = S[sid] = {"sid": sid, "cid": e["client_id"], "run": e.get("run_id"), "device": e["device_category"],
                          "landing": None, "events": [], "steps": set(), "revenue": 0.0, "orders": 0,
                          "exposures": {}, "page_types": [], "items_added": 0}
        s["events"].append(e)
        n = e["event"]
        if n == "page_view":
            s["page_types"].append(e.get("page_type"))
            if s["landing"] is None:
                s["landing"] = e.get("page_type")
        if n == "experiment_impression":
            s["exposures"].setdefault(e["experiment_id"], e["variant_id"])
        if n in ("sign_up", "checkout_contact"):
            s["steps"].add("checkout_step1")
        if n == "add_to_cart":
            s["items_added"] += 1
        if n == "purchase":
            s["revenue"] += e.get("value", 0)
            s["orders"] += 1
        s["steps"].add(n)
    for s in S.values():
        s["steps"].add("session")
        s["bounced"] = len(s["page_types"]) <= 1
    return list(S.values())


# ---------------- stats ----------------
def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def two_prop(x1, n1, x2, n2):
    """returns (p_control, p_variant, rel_uplift, ci_low, ci_high (relative, approx), p_value two-sided)"""
    if n1 == 0 or n2 == 0:
        return None
    p1, p2 = x1 / n1, x2 / n2
    pp = (x1 + x2) / (n1 + n2)
    se = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2)) or 1e-12
    z = (p2 - p1) / se
    pval = 2 * (1 - norm_cdf(abs(z)))
    se_d = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    lo, hi = (p2 - p1) - 1.96 * se_d, (p2 - p1) + 1.96 * se_d
    rel = (p2 / p1 - 1) if p1 else float("nan")
    return dict(cr_c=p1, cr_v=p2, uplift=rel, abs_ci=(lo, hi),
                rel_ci=((lo / p1) if p1 else None, (hi / p1) if p1 else None), p=pval, z=z)


def prob_beat(x1, n1, x2, n2, draws=40000, seed=1):
    rnd = random.Random(seed)
    w = 0
    for _ in range(draws):
        a = rnd.betavariate(1 + x1, 1 + n1 - x1)
        b = rnd.betavariate(1 + x2, 1 + n2 - x2)
        w += b > a
    return w / draws


def welch(a, b):
    """Welch t-test (normal approx) on per-unit values (e.g. revenue per visitor). returns diff, rel, p"""
    import statistics as st
    if len(a) < 2 or len(b) < 2:
        return None
    ma, mb = st.fmean(a), st.fmean(b)
    va, vb = st.pvariance(a), st.pvariance(b)
    se = math.sqrt(va / len(a) + vb / len(b)) or 1e-12
    z = (mb - ma) / se
    return dict(mean_c=ma, mean_v=mb, rel=(mb / ma - 1) if ma else float("nan"), p=2 * (1 - norm_cdf(abs(z))), z=z)


def srm_p(counts, weights):
    tot = sum(counts)
    chi = sum((c - tot * w) ** 2 / (tot * w) for c, w in zip(counts, weights) if w > 0)
    k = len(counts) - 1
    # chi-square survival for k dof (k small): use Wilson-Hilferty approx
    if k <= 0:
        return 1.0
    zz = ((chi / k) ** (1 / 3) - (1 - 2 / (9 * k))) / math.sqrt(2 / (9 * k))
    return 1 - norm_cdf(zz)
