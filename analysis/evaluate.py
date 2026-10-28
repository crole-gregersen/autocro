#!/usr/bin/env python3
"""Evaluate running experiments against config/decision-rules.json and (with --apply) act on decisions.
Usage: python3 analysis/evaluate.py [--apply]
Metrics are session/visitor-level among visitors exposed to the experiment (experiment_impression).
Metric names: any funnel step (e.g. purchase, add_to_cart, begin_checkout) = share of exposed visitors
reaching it; 'rpv' = revenue per exposed visitor; 'aov' = average order value (reported only).
"""
import argparse, json, os, datetime
from common import ROOT, load_events, build_sessions, two_prop, prob_beat, welch, srm_p

ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true"); a = ap.parse_args()
RULES = json.load(open(os.path.join(ROOT, "config/decision-rules.json")))
REG_P = os.path.join(ROOT, "site/config/experiments.json")
CFG_P = os.path.join(ROOT, "site/config/site-config.json")
REG = json.load(open(REG_P)); CFG = json.load(open(CFG_P))
S = build_sessions(load_events())
today = datetime.date.today().isoformat()
pct = lambda x: f"{100 * x:+.1f}%" if x == x else "n/a"


def metric_counts(ss, m):
    return sum(m in s["steps"] for s in ss)


def evaluate(exp):
    groups = {v["id"]: [] for v in exp["variants"]}
    for s in S:
        v = s["exposures"].get(exp["id"])
        if v in groups: groups[v].append(s)
    ctrl = exp["variants"][0]["id"]
    res = {"id": exp["id"], "n": {k: len(v) for k, v in groups.items()}, "variants": {}}
    weights = [v["weight"] / 100 for v in exp["variants"]]
    res["srm_p"] = srm_p([len(groups[v["id"]]) for v in exp["variants"]], weights)
    C = groups[ctrl]
    for v in exp["variants"][1:]:
        V = groups[v["id"]]; r = {}
        for m in [exp["primary_metric"]] + exp.get("secondary_metrics", []) + [g for g in exp.get("guardrails", []) if g != "rpv"]:
            t = two_prop(metric_counts(C, m), len(C), metric_counts(V, m), len(V))
            if t:
                t["prob_beat"] = prob_beat(metric_counts(C, m), len(C), metric_counts(V, m), len(V))
                t["x"] = (metric_counts(C, m), metric_counts(V, m))
            r[m] = t
        r["rpv"] = welch([s["revenue"] for s in C], [s["revenue"] for s in V])
        oc = [s["revenue"] / s["orders"] for s in C if s["orders"]]; ov = [s["revenue"] / s["orders"] for s in V if s["orders"]]
        r["aov"] = welch(oc, ov)
        res["variants"][v["id"]] = r
    return res


def decide(exp, res):
    R = {**RULES, **exp.get("rule_overrides", {})}; n = res["n"]; ctrl = exp["variants"][0]["id"]
    if res["srm_p"] < R["srm_p_threshold"]:
        return "invalid", None, f"R1 SRM detected (p={res['srm_p']:.2g}); counts {n}"
    if min(n.values()) < R["min_exposed_per_variant"]:
        return "continue", None, f"R2 waiting for sample: {n} (need {R['min_exposed_per_variant']}/variant)"
    best, best_reason = None, ""
    any_alive = False
    for vid, r in res["variants"].items():
        pm = r[exp["primary_metric"]]
        if pm is None: continue
        if pm["uplift"] < 0 and pm["p"] < R["alpha"]:
            continue  # significantly worse
        ok = pm["uplift"] > R["min_relative_uplift"] and pm["p"] < R["alpha"] and pm["prob_beat"] >= R["min_prob_to_beat"]
        if not ok:
            any_alive = True; continue
        harmed = []
        for g in exp.get("guardrails", []):
            if g == exp["primary_metric"]: continue
            gr = r.get(g)
            if not gr: continue
            rel = gr.get("uplift", gr.get("rel"))
            if (rel < 0 and gr["p"] < R["guardrail_harm_alpha"]) or rel < -R["guardrail_max_relative_drop"]:
                harmed.append(f"{g} {pct(rel)} (p={gr['p']:.3f})")
        if harmed:
            best_reason += f" R4 variant {vid} wins primary but harms guardrail(s): {', '.join(harmed)}."
            continue
        if best is None or pm["uplift"] > res["variants"][best][exp["primary_metric"]]["uplift"]:
            best = vid
    if best:
        pm = res["variants"][best][exp["primary_metric"]]
        return "ship", best, f"R3 {best} beats {ctrl} on {exp['primary_metric']}: {pct(pm['uplift'])} (p={pm['p']:.4f}, P(beat)={pm['prob_beat']:.3f}); guardrails OK."
    if max(n.values()) >= R["max_exposed_per_variant"] or not any_alive:
        return "stop", None, ("R5 no variant significantly better — " + ("all variants significantly worse or blocked." if not any_alive else "max sample reached; keep control.")) + best_reason
    return "continue", None, "No decision yet: not significant." + best_reason


def fmt(exp, res):
    L = [f"### {exp['id']} — {exp['name']}", f"Exposed visitors: {res['n']} · SRM p={res['srm_p']:.3f}", "",
         "| Variant | Metric | Control | Variant | Rel. uplift | 95% CI (rel) | p | P(beat) |", "|---|---|---|---|---|---|---|---|"]
    for vid, r in res["variants"].items():
        for m, t in r.items():
            if not t: continue
            if "cr_c" in t:
                lo, hi = t["rel_ci"]
                L.append(f"| {vid} | {m} | {100*t['cr_c']:.2f}% | {100*t['cr_v']:.2f}% | {pct(t['uplift'])} | {pct(lo)} … {pct(hi)} | {t['p']:.4f} | {t['prob_beat']:.3f} |")
            else:
                L.append(f"| {vid} | {m} | €{t['mean_c']:.2f} | €{t['mean_v']:.2f} | {pct(t['rel'])} | | {t['p']:.4f} | |")
    return "\n".join(L)


report = [f"# Experiment evaluation — {today}\n"]
decisions = []
for exp in REG["experiments"]:
    if exp["status"] != "running": continue
    res = evaluate(exp); d, winner, why = decide(exp, res)
    report += [fmt(exp, res), f"\n**Decision: {d.upper()}** — {why}\n"]
    decisions.append((exp, d, winner, why, res))

if a.apply:
    log_p = os.path.join(ROOT, "docs/decision-log.md")
    if not os.path.exists(log_p):
        open(log_p, "w").write("# AutoCRO decision log\n\n")
    for exp, d, winner, why, res in decisions:
        if d == "continue": continue
        exp["status"] = {"ship": "shipped", "stop": "stopped", "invalid": "invalid"}[d]
        exp["concluded"] = today; exp["decision"] = why; exp["winner"] = winner
        exp["final_n"] = res["n"]
        if d == "ship":
            v = next(v for v in exp["variants"] if v["id"] == winner)
            dev = (exp.get("targeting") or {}).get("device", "all")
            if dev == "all":
                CFG["features"].update(v.get("features", {}))
            else:  # ship only to the device the test was run on
                CFG.setdefault("device_features", {}).setdefault(dev, {}).update(v.get("features", {}))
            if v.get("css"): CFG["css"] = (CFG.get("css", "") + "\n/* " + exp["id"] + " */\n" + v["css"]).strip()
            CFG.setdefault("changelog", []).append({"date": today, "experiment": exp["id"], "name": exp["name"], "features": v.get("features", {}), "scope": dev})
        with open(log_p, "a") as f:
            f.write(f"## {today} · {exp['id']} {exp['name']} → **{d.upper()}**\n\n- Hypothesis: {exp.get('hypothesis','')}\n- {why}\n- Exposed: {res['n']}\n\n")
        with open(os.path.join(ROOT, "data/decisions.jsonl"), "a") as f:
            f.write(json.dumps({"date": today, "experiment": exp["id"], "decision": d, "winner": winner, "reason": why, "n": res["n"]}) + "\n")
    json.dump(REG, open(REG_P, "w"), indent=2)
    json.dump(CFG, open(CFG_P, "w"), indent=2)

p = os.path.join(ROOT, "reports", f"evaluation-{today}.md")
os.makedirs(os.path.dirname(p), exist_ok=True)
open(p, "w").write("\n".join(report) + "\n")
print("\n".join(report))
