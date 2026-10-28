#!/usr/bin/env python3
"""Build the AutoCRO engine-room dashboard (single self-contained HTML) from the repo's data.
Usage: python3 dashboard/build.py  ->  dashboard/dist/autocro-dashboard.html
Reads only analyst-side data (data/events, configs, docs, reports). Never reads sim/sealed."""
import json, os, re, sys, glob, html, datetime, statistics
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis"))
from common import ROOT, FUNNEL, load_events, build_sessions, two_prop, prob_beat, srm_p, welch

SITE = "https://crole-gregersen.github.io/autocro/"
REPO = "https://github.com/crole-gregersen/autocro"
GA4 = "https://analytics.google.com/analytics/web/#/a56822588p561157387/realtime/overview"
J = lambda p: json.load(open(os.path.join(ROOT, p)))
esc = lambda s: html.escape(str(s))
CFG, REG, RULES, QUEUE = J("site/config/site-config.json"), J("site/config/experiments.json"), J("config/decision-rules.json"), J("sim/queue.json")
DECISIONS = [json.loads(l) for l in open(os.path.join(ROOT, "data/decisions.jsonl"))] if os.path.exists(os.path.join(ROOT, "data/decisions.jsonl")) else []
ORIGINAL = {"pdp_gallery_layout": "tall", "pdp_shipping_info": False, "cart_shipping_info": False, "free_shipping_bar": False,
            "checkout_guest": False, "plp_show_ratings": False, "pdp_show_reviews": False, "sticky_atc_mobile": False,
            "atc_button_text": "Add to bag", "atc_button_color": "dark", "newsletter_popup": False, "home_hero_cta": "Explore the collection"}
LOCAL_RUNS = {"R001", "R002", "R003", "R004"}  # ran in the Claude sandbox before the live setup

# ---------------- data ----------------
evs = load_events()
S = build_sessions(evs)
by_run = {}
for s in S: by_run.setdefault(s["run"], []).append(s)
ev_count = {}
for e in evs: ev_count[e["run_id"]] = ev_count.get(e["run_id"], 0) + 1


def kpi(ss):
    n = len(ss) or 1; o = sum(s["orders"] for s in ss); r = sum(s["revenue"] for s in ss)
    return dict(n=len(ss), cr=sum(s["orders"] > 0 for s in ss) / n, atc=sum("add_to_cart" in s["steps"] for s in ss) / n,
                rpv=r / n, aov=r / o if o else 0, orders=o, revenue=r, bounce=sum(s["bounced"] for s in ss) / n)


runs = []
for rid in sorted(by_run):
    ss = by_run[rid]; k = kpi(ss)
    ts = [e["ts"] for s in ss for e in s["events"]]
    exps = sorted({x for s in ss for x in s["exposures"]})
    running_exps = sorted({x for s in ss for x, v in s["exposures"].items()})
    audit_p = os.path.join(ROOT, "reports", f"ga-audit-{rid}.json")
    ga = None
    if os.path.exists(audit_p):
        a = json.load(open(audit_p)); sent = sum(v for kk, v in a["events_sent"].items() if kk != "?")
        ga = sent / ev_count[rid] if ev_count.get(rid) else None
    kind = "experiment" if exps else ("baseline" if rid in ("R001", "R002") or k["n"] >= 1000 else "smoke test")
    runs.append(dict(id=rid, **k, events=ev_count.get(rid, 0), start=min(ts), end=max(ts), exps=exps, kind=kind,
                     where="sandbox" if rid in LOCAL_RUNS else "GitHub Actions → live site", ga=ga))

total_sessions = sum(r["n"] for r in runs); total_events = sum(r["events"] for r in runs)
total_orders = sum(r["orders"] for r in runs)
base_runs = [r for r in runs if r["id"] in ("R001", "R002")]
baseline = kpi([s for r in base_runs for s in by_run[r["id"]]])
full_clean = [r for r in runs if r["kind"] == "baseline" and r["id"] not in ("R001", "R002")]
latest = full_clean[-1] if full_clean else runs[-1]
latest_ss = by_run[latest["id"]]
ga_runs = [r for r in runs if r["ga"] is not None]
ga_latest = ga_runs[-1] if ga_runs else None


def funnel(ss):
    n = len(ss) or 1
    return [sum(st in s["steps"] for s in ss) / n for st in FUNNEL]


f_base = funnel([s for r in base_runs for s in by_run[r["id"]]]); f_now = funnel(latest_ss)


# experiment stats (same method as analysis/evaluate.py)
def exp_stats(exp):
    groups = {v["id"]: [] for v in exp["variants"]}
    for s in S:
        v = s["exposures"].get(exp["id"])
        if v in groups: groups[v].append(s)
    ctrl = exp["variants"][0]["id"]; C = groups[ctrl]; m = exp["primary_metric"]
    out = []
    for v in exp["variants"]:
        V = groups[v["id"]]; xv = sum(m in s["steps"] for s in V)
        row = dict(id=v["id"], weight=v["weight"], n=len(V), rate=xv / len(V) if V else 0, features=v.get("features", {}),
                   rpv=(sum(s["revenue"] for s in V) / len(V)) if V else 0, control=v["id"] == ctrl)
        if v["id"] != ctrl and C and V:
            t = two_prop(sum(m in s["steps"] for s in C), len(C), xv, len(V))
            row.update(uplift=t["uplift"], ci=t["rel_ci"], p=t["p"], pbeat=prob_beat(sum(m in s["steps"] for s in C), len(C), xv, len(V), draws=20000))
        out.append(row)
    runs_live = sorted({s["run"] for vv in groups.values() for s in vv})
    srm = srm_p([len(groups[v["id"]]) for v in exp["variants"]], [v["weight"] / 100 for v in exp["variants"]]) if sum(len(g) for g in groups.values()) else 1
    return out, runs_live, srm


def backlog():
    p = os.path.join(ROOT, "docs/hypothesis-backlog.md")
    rows = []
    for line in open(p):
        if line.startswith("| ") and not line.startswith("| #") and not line.startswith("|---"):
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(c) >= 6: rows.append(c)
    return rows


# ---------------- formatting ----------------
pc = lambda x, d=1: f"{100 * x:.{d}f}%"
eur = lambda x: f"€{x:,.2f}"
sgn = lambda x: f"{100 * x:+.1f}%"
dt = lambda ms: datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=1))).strftime("%d %b %H:%M")
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).strftime("%d %b %Y, %H:%M CET")


def status_badge(st):
    icon = {"running": "▶", "shipped": "✓", "stopped": "■", "invalid": "!"}.get(st, "•")
    return f'<span class="badge st-{esc(st)}"><span aria-hidden="true">{icon}</span> {esc(st.capitalize())}</span>'


def preview(exp, vid, path="#/"):
    return f"{SITE}?ac_preview={exp['id']}:{vid}{path}"


ROUTE_PATH = {"p": "#/p/P001", "cart": "#/cart", "checkout": "#/checkout", "c": "#/c/jackets", "home": "#/", "": "#/"}


# ---------------- charts (inline SVG) ----------------
def cr_chart():
    W, H, L, R, T, B = 760, 260, 48, 16, 18, 46
    pts = runs; n = len(pts)
    ymax = max(0.16, max(r["cr"] for r in pts) * 1.15)
    x = lambda i: L + (W - L - R) * (i / (n - 1 if n > 1 else 1))
    y = lambda v: T + (H - T - B) * (1 - v / ymax)
    g = []
    for t in [0, 0.04, 0.08, 0.12, 0.16, 0.20]:
        if t > ymax: break
        g.append(f'<line x1="{L}" x2="{W - R}" y1="{y(t):.1f}" y2="{y(t):.1f}" class="grid"/><text x="{L - 8}" y="{y(t) + 4:.1f}" class="tick" text-anchor="end">{int(t * 100)}%</text>')
    # ship markers: between last run before decision and first after
    ships = [d for d in DECISIONS if d["decision"] == "ship"]
    if ships:
        i = next((k for k, r in enumerate(pts) if r["id"] == "R005"), None)
        if i:
            xm = (x(i - 1) + x(i)) / 2
            g.append(f'<line x1="{xm:.1f}" x2="{xm:.1f}" y1="{T}" y2="{H - B}" class="marker"/><text x="{xm + 6:.1f}" y="{T + 10}" class="ann">3 tests shipped · EXP001–003</text>')
        i3 = next((k for k, r in enumerate(pts) if r["id"] == "R003"), None)
        if i3:
            g.append(f'<rect x="{x(i3) - 14:.1f}" y="{T}" width="{x(i3 + 1) - x(i3) + 28:.1f}" height="{H - T - B}" class="band"/><text x="{x(i3) - 10:.1f}" y="{H - B - 6}" class="ann">A/B tests running</text>')
    path = " ".join(f"{'M' if i == 0 else 'L'}{x(i):.1f},{y(r['cr']):.1f}" for i, r in enumerate(pts))
    g.append(f'<path d="{path}" class="line"/>')
    for i, r in enumerate(pts):
        small = r["kind"] == "smoke test"
        tip = f"{r['id']} · {r['kind']} · {r['n']:,} sessions|Conversion {pc(r['cr'])} · RPV {eur(r['rpv'])}|{dt(r['start'])} · {r['where']}"
        g.append(f'<g class="pt" data-tip="{esc(tip)}"><circle cx="{x(i):.1f}" cy="{y(r["cr"]):.1f}" r="14" class="hit"/>'
                 f'<circle cx="{x(i):.1f}" cy="{y(r["cr"]):.1f}" r="{4 if small else 5}" class="dot{" hollow" if small else ""}"/></g>'
                 f'<text x="{x(i):.1f}" y="{H - B + 18}" class="tick" text-anchor="middle">{r["id"]}</text>')
    lab_i = n - 1
    g.append(f'<text x="{x(lab_i) - 8:.1f}" y="{y(pts[lab_i]["cr"]) - 12:.1f}" class="dlabel" text-anchor="end">{pc(pts[lab_i]["cr"])}</text>')
    g.append(f'<text x="{x(0) + 8:.1f}" y="{y(pts[0]["cr"]) + 18:.1f}" class="dlabel">{pc(pts[0]["cr"])}</text>')
    g.append(f'<text x="{L}" y="{H - 6}" class="tick">Hollow dots = small smoke-test runs (GA4 checks, &lt;1,000 sessions) — noisier.</text>')
    return f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="Conversion rate per traffic run">{"".join(g)}</svg>'


def funnel_chart():
    labels = ["Sessions", "Viewed product", "Added to bag", "Viewed bag", "Began checkout", "Checkout step 1", "Delivery info", "Payment info", "Purchase"]
    W, rowh, L, R, T = 470, 36, 112, 52, 34
    H = T + rowh * len(labels) + 10
    sx = lambda v: (W - L - R) * v
    g = [f'<g class="legend"><rect x="{L}" y="6" width="12" height="12" rx="3" class="s1"/><text x="{L + 18}" y="16" class="tick">Original (R001–R002)</text>'
         f'<rect x="{L + 150}" y="6" width="12" height="12" rx="3" class="s2"/><text x="{L + 168}" y="16" class="tick">Current ({latest["id"]})</text></g>']
    for i, (lab, a, b) in enumerate(zip(labels, f_base, f_now)):
        yy = T + i * rowh
        g.append(f'<text x="{L - 10}" y="{yy + 18}" class="tick" text-anchor="end">{lab}</text>')
        for j, (v, cls) in enumerate(((a, "s1"), (b, "s2"))):
            tip = f"{lab}|{'Original baseline' if j == 0 else 'Current shop'}: {pc(v)} of sessions"
            g.append(f'<g class="pt" data-tip="{esc(tip)}"><rect x="{L}" y="{yy + 3 + j * 13}" width="{max(sx(v), 2):.1f}" height="11" rx="3" class="{cls}"/></g>')
        g.append(f'<text x="{L + sx(max(a, b)) + 6:.1f}" y="{yy + 21}" class="dlabel">{pc(b)} <tspan class="tick">was {pc(a)}</tspan></text>')
    return f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="Funnel, original vs current">{"".join(g)}</svg>'


def ci_bar(row, shipped_winner):
    """mini forest plot: relative uplift with 95% CI on a shared -40%..+100% scale"""
    lo_s, hi_s, W, H = -0.4, 1.0, 220, 26
    X = lambda v: 6 + (W - 12) * (min(max(v, lo_s), hi_s) - lo_s) / (hi_s - lo_s)
    lo, hi = row["ci"]; u = row["uplift"]
    sig = row["p"] < RULES["alpha"]
    cls = "good" if sig and u > 0 else "bad" if sig and u < 0 else "neutral"
    return (f'<svg viewBox="0 0 {W} {H}" class="ci" role="img" aria-label="Uplift {sgn(u)}, 95% CI {sgn(lo)} to {sgn(hi)}">'
            f'<line x1="{X(0):.1f}" x2="{X(0):.1f}" y1="2" y2="{H - 2}" class="zero"/>'
            f'<line x1="{X(lo):.1f}" x2="{X(hi):.1f}" y1="{H / 2}" y2="{H / 2}" class="whisk {cls}"/>'
            f'<circle cx="{X(u):.1f}" cy="{H / 2}" r="5" class="pnt {cls}"/></svg>')


# ---------------- sections ----------------
def tiles():
    up = latest["cr"] / baseline["cr"] - 1
    rpv_up = latest["rpv"] / baseline["rpv"] - 1
    n_ship = sum(e["status"] == "shipped" for e in REG["experiments"]); n_run = sum(e["status"] == "running" for e in REG["experiments"])
    n_stop = sum(e["status"] in ("stopped", "invalid") for e in REG["experiments"])
    T = [("Conversion rate now", pc(latest["cr"]), f"was {pc(baseline['cr'])} at baseline · <b class='up'>{sgn(up)}</b>", f"{latest['id']}, {latest['n']:,} sessions"),
         ("Revenue per visitor", eur(latest["rpv"]), f"was {eur(baseline['rpv'])} · <b class='up'>{sgn(rpv_up)}</b>", "simulated EUR"),
         ("Experiments", f"{len(REG['experiments'])}", f"{n_ship} shipped · {n_run} running · {n_stop} stopped", "decided by rules R1–R7"),
         ("Simulated shoppers", f"{total_sessions:,}", f"{len(runs)} traffic runs · {total_events:,} events", f"{total_orders:,} simulated orders"),
         ("GA4 delivery", pc(ga_latest["ga"], 0) if ga_latest else "–", f"of events reach GA4 ({ga_latest['id'] if ga_latest else ''})", "own event log is source of truth")]
    return "".join(f'<div class="tile"><div class="tl">{a}</div><div class="tv">{b}</div><div class="ts">{c}</div><div class="tm">{d}</div></div>' for a, b, c, d in T)


def experiments_html():
    out = []
    for exp in sorted(REG["experiments"], key=lambda e: e["id"], reverse=True):
        rows, runs_live, srm = exp_stats(exp)
        tgt = exp.get("targeting", {}).get("device", "all")
        path = ROUTE_PATH.get(exp.get("exposure_route", ""), "#/")
        trs = []
        for r in rows:
            feats = ", ".join(f"{k} = {json.dumps(v)}" for k, v in (r["features"] or {}).items()) or ("current shop (no change)" if r["control"] else "—")
            if r["control"] and exp.get("control_features"):
                feats = "original: " + ", ".join(f"{k} = {json.dumps(v)}" for k, v in exp["control_features"].items())
            win = exp.get("winner") == r["id"]
            stat = (f'<td class="num">{sgn(r["uplift"])}</td><td>{ci_bar(r, win)}</td><td class="num">{r["p"]:.4f}</td><td class="num">{r["pbeat"]:.3f}</td>'
                    if not r["control"] and "uplift" in r else '<td class="muted" colspan="4">reference</td>')
            trs.append(f'<tr class="{"win" if win else ""}"><td><b>{esc(r["id"])}</b>{" <span class=\"badge st-shipped\">✓ winner</span>" if win else ""}<div class="feat">{esc(feats)}</div></td>'
                       f'<td class="num">{r["weight"]}%</td><td class="num">{r["n"]:,}</td><td class="num">{pc(r["rate"], 2)}</td>{stat}'
                       f'<td><a href="{esc(preview(exp, r["id"], path))}" target="_blank" rel="noopener">Preview ↗</a></td></tr>')
        out.append(f'''<details class="exp" {"open" if exp["status"] == "running" or exp is sorted(REG["experiments"], key=lambda e: e["id"])[-1] else ""}>
<summary><span class="eid">{esc(exp["id"])}</span> <span class="ename">{esc(exp["name"])}</span> {status_badge(exp["status"])}
<span class="emeta">{esc(exp["primary_metric"])} · {esc(tgt)} · page: {esc(exp.get("exposure_route") or "all")}</span></summary>
<p class="hyp"><b>Hypothesis.</b> {esc(exp.get("hypothesis", ""))}</p>
<p class="ev"><b>Evidence.</b> {esc(exp.get("evidence", ""))}</p>
<table class="vt"><thead><tr><th>Variant</th><th class="num">Split</th><th class="num">Exposed</th><th class="num">{esc(exp["primary_metric"])}</th><th class="num">Uplift</th><th>95% CI <span class="muted">(−40% … +100%)</span></th><th class="num">p</th><th class="num">P(beat)</th><th>Live view</th></tr></thead>
<tbody>{"".join(trs)}</tbody></table>
<p class="dec"><b>Decision.</b> {esc(exp.get("decision", "Running — evaluated after every traffic run."))}
<span class="muted"> · Traffic runs: {esc(", ".join(runs_live) or "none yet")} · SRM p = {srm:.3f}{" · concluded " + esc(exp["concluded"]) if exp.get("concluded") else ""}</span></p>
</details>''')
    return "".join(out)


def runs_table():
    trs = []
    for r in reversed(runs):
        trs.append(f'<tr><td><b>{r["id"]}</b></td><td>{dt(r["start"])}</td><td>{esc(r["kind"])}</td><td>{esc(", ".join(r["exps"]) or "—")}</td>'
                   f'<td class="num">{r["n"]:,}</td><td class="num">{r["events"]:,}</td><td class="num">{r["orders"]:,}</td><td class="num">{pc(r["cr"])}</td>'
                   f'<td class="num">{eur(r["rpv"])}</td><td class="num">{pc(r["ga"], 0) if r["ga"] is not None else "—"}</td><td class="muted">{esc(r["where"])}</td></tr>')
    return "".join(trs)


def config_html():
    eff = dict(CFG["features"]); out = []
    for k, v in CFG["features"].items():
        dv = {d: f.get(k) for d, f in CFG.get("device_features", {}).items() if k in f}
        changed = v != ORIGINAL.get(k) or dv
        val = json.dumps(v) + "".join(f' <span class="pill">{d}: {json.dumps(x)}</span>' for d, x in dv.items())
        src = next((c for c in CFG.get("changelog", []) if k in c.get("features", {})), None)
        out.append(f'<tr class="{"chg" if changed else ""}"><td><code>{esc(k)}</code></td><td><code>{val}</code></td><td class="muted"><code>{esc(json.dumps(ORIGINAL.get(k)))}</code></td>'
                   f'<td>{(esc(src["experiment"]) + " · " + esc(src["date"])) if src else ""}</td></tr>')
    return "".join(out)


def backlog_html():
    return "".join(f'<tr><td class="num">{esc(c[0])}</td><td>{esc(c[1])}</td><td>{esc(c[2])}</td><td>{esc(c[3])}</td><td class="num">{esc(c[4])}</td><td>{esc(c[5])}</td></tr>' for c in backlog())


def rules_html():
    keys = [("min_exposed_per_variant", "Min. exposed visitors per variant"), ("max_exposed_per_variant", "Max. per variant (then stop)"),
            ("alpha", "Significance level α"), ("min_prob_to_beat", "Min. probability to beat control"), ("srm_p_threshold", "SRM alarm p"),
            ("guardrail_harm_alpha", "Guardrail harm α"), ("max_concurrent_experiments", "Max. concurrent tests")]
    p = "".join(f'<div class="kv"><span>{b}</span><b>{RULES[a]}</b></div>' for a, b in keys)
    rl = "".join(f"<li>{esc(r)}</li>" for r in RULES["rules"])
    return p, rl


def timeline_html():
    items = json.load(open(os.path.join(ROOT, "docs/timeline.json")))
    return "".join(f'<li><span class="td">{esc(a)}</span><b>{esc(b)}</b><span>{esc(c)}</span></li>' for a, b, c in items)


rules_kv, rules_list = rules_html()
running = [e for e in REG["experiments"] if e["status"] == "running"]
last_run = runs[-1]
queue_txt = f'{QUEUE.get("run_id")} · {QUEUE.get("sessions"):,} sessions' if QUEUE.get("run_id") else "none"
engine_state = ("Testing: " + ", ".join(e["id"] for e in running)) if running else "Idle — between cycles (next: cycle 2 ideation)"

HTML = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AutoCRO — engine room</title>
<style>
.viz-root{{color-scheme:light;--plane:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);
--s1:#2a78d6;--s2:#eb6834;--good:#0ca30c;--goodtxt:#006300;--warn:#fab219;--serious:#ec835a;--crit:#d03b3b;--neutral:#898781;--band:rgba(42,120,214,.06)}}
@media (prefers-color-scheme:dark){{:root:where(:not([data-theme="light"])) .viz-root{{color-scheme:dark;--plane:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);--s1:#3987e5;--s2:#d95926;--goodtxt:#0ca30c;--band:rgba(57,135,229,.10)}}}}
*{{box-sizing:border-box}} body{{margin:0}}
.viz-root{{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--plane);color:var(--ink);min-height:100vh;padding:28px clamp(14px,3vw,40px) 60px}}
.wrap{{max-width:1180px;margin:0 auto}}
header{{display:flex;flex-wrap:wrap;gap:12px 28px;align-items:flex-end;justify-content:space-between;margin-bottom:22px}}
h1{{font-size:26px;margin:0}} h1 small{{display:block;font-size:13px;font-weight:500;color:var(--ink2);margin-top:4px}}
h2{{font-size:17px;margin:0 0 4px}} .sub{{color:var(--ink2);font-size:13px;margin:0 0 14px}}
.links a{{display:inline-block;margin-left:6px;padding:7px 12px;border:1px solid var(--border);border-radius:6px;background:var(--surface);color:var(--ink);text-decoration:none;font-size:13px;font-weight:600}}
.state{{display:flex;flex-wrap:wrap;gap:8px 22px;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px 16px;font-size:13px;margin-bottom:18px}}
.state b{{font-weight:650}} .dotlive{{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--good);margin-right:6px}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:18px}}
.tile{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px 16px}}
.tl{{font-size:12px;color:var(--ink2);font-weight:600;text-transform:uppercase;letter-spacing:.04em}} .tv{{font-size:30px;font-weight:700;margin:6px 0 2px}}
.ts{{font-size:13px;color:var(--ink2)}} .tm{{font-size:12px;color:var(--muted);margin-top:4px}} .up{{color:var(--goodtxt)}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:18px;margin-bottom:18px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:18px}} @media (max-width:900px){{.grid2{{grid-template-columns:1fr}}}}
.chart{{width:100%;height:auto;display:block}} .chart text{{font-family:inherit}}
.grid{{stroke:var(--grid);stroke-width:1}} .tick{{fill:var(--muted);font-size:11px}} .dlabel{{fill:var(--ink);font-size:12px;font-weight:650}}
.ann{{fill:var(--ink2);font-size:11px}} .marker{{stroke:var(--axis);stroke-width:1.5;stroke-dasharray:4 3}} .band{{fill:var(--band)}}
.line{{fill:none;stroke:var(--s1);stroke-width:2}} .dot{{fill:var(--s1);stroke:var(--surface);stroke-width:2}} .dot.hollow{{fill:var(--surface);stroke:var(--s1)}}
.hit{{fill:transparent}} .s1{{fill:var(--s1)}} .s2{{fill:var(--s2)}}
.pt{{cursor:default}} .pt:hover .dot{{r:7}} .pt:hover rect{{opacity:.85}}
#tip{{position:fixed;pointer-events:none;background:var(--ink);color:var(--plane);font-size:12px;line-height:1.45;padding:7px 10px;border-radius:6px;opacity:0;transition:opacity .1s;z-index:9;max-width:300px}}
table{{width:100%;border-collapse:collapse;font-size:13px}} th{{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--ink2);font-weight:650;border-bottom:1px solid var(--axis);padding:7px 8px}}
td{{border-bottom:1px solid var(--grid);padding:8px;vertical-align:top}} .num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}} .muted{{color:var(--muted)}}
.scroll{{overflow-x:auto}}
.badge{{display:inline-block;font-size:11px;font-weight:700;padding:2px 8px;border-radius:10px;white-space:nowrap;vertical-align:middle}}
.st-shipped{{background:var(--good);color:#fff}} .st-running{{background:var(--s1);color:#fff}} .st-stopped{{background:var(--neutral);color:#fff}} .st-invalid{{background:var(--crit);color:#fff}}
details.exp{{border:1px solid var(--border);border-radius:8px;margin-bottom:10px;background:var(--surface)}}
details.exp summary{{cursor:pointer;padding:12px 14px;display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center}}
.eid{{font-weight:800}} .ename{{font-weight:600}} .emeta{{color:var(--muted);font-size:12px;margin-left:auto}}
details.exp > :not(summary){{margin-left:14px;margin-right:14px}} .hyp,.ev,.dec{{font-size:13px;color:var(--ink2);margin:6px 14px}} .dec{{margin-bottom:14px}}
.vt tr.win td{{background:rgba(12,163,12,.06)}} .feat{{font-size:12px;color:var(--muted);margin-top:2px;font-family:ui-monospace,Menlo,monospace}}
.ci{{width:220px;height:26px}} .zero{{stroke:var(--axis);stroke-width:1.5}} .whisk{{stroke-width:2;stroke-linecap:round}}
.whisk.good{{stroke:var(--good)}} .whisk.bad{{stroke:var(--crit)}} .whisk.neutral{{stroke:var(--neutral)}}
.pnt{{stroke:var(--surface);stroke-width:2}} .pnt.good{{fill:var(--good)}} .pnt.bad{{fill:var(--crit)}} .pnt.neutral{{fill:var(--neutral)}}
a{{color:var(--s1)}} code{{font-family:ui-monospace,Menlo,monospace;font-size:12px}} tr.chg td{{background:rgba(42,120,214,.06)}}
.pill{{font-size:11px;background:var(--grid);border-radius:8px;padding:1px 6px;margin-left:4px}}
.pipe{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;counter-reset:s}}
.step{{border:1px solid var(--border);border-radius:8px;padding:10px 12px;font-size:12px;color:var(--ink2);position:relative}} .step b{{display:block;color:var(--ink);font-size:13px;margin-bottom:3px}}
.step b::before{{counter-increment:s;content:counter(s) ". ";color:var(--muted)}}
.kvs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:6px 18px;margin-bottom:10px}} .kv{{display:flex;justify-content:space-between;border-bottom:1px solid var(--grid);padding:5px 0;font-size:13px}}
ol.rules{{font-size:13px;color:var(--ink2);padding-left:18px;margin:8px 0 0}} ol.rules li{{margin:3px 0}}
ul.tline{{list-style:none;padding:0;margin:0;font-size:13px}} ul.tline li{{display:grid;grid-template-columns:60px 170px 1fr;gap:10px;padding:7px 0;border-bottom:1px solid var(--grid)}} .td{{color:var(--muted)}}
@media (max-width:700px){{ul.tline li{{grid-template-columns:1fr}}}}
footer{{font-size:12px;color:var(--muted);margin-top:24px}}
</style></head><body><div class="viz-root"><div class="wrap">
<header><h1>AutoCRO — engine room<small>Self-optimising webshop proof of concept · Fjeldspor (fictional) · built and operated by Claude for IMPACT Commerce</small></h1>
<div class="links"><a href="{SITE}" target="_blank" rel="noopener">Live shop ↗</a><a href="{REPO}" target="_blank" rel="noopener">Repo ↗</a><a href="{REPO}/actions" target="_blank" rel="noopener">Traffic runs ↗</a><a href="{GA4}" target="_blank" rel="noopener">GA4 ↗</a></div></header>

<div class="state"><span><span class="dotlive" aria-hidden="true"></span><b>Engine state:</b> {esc(engine_state)}</span>
<span><b>Last traffic run:</b> {last_run["id"]} · {dt(last_run["end"])}</span><span><b>Last queued:</b> {esc(queue_txt)}</span>
<span><b>Tests decided:</b> {sum(e["status"] != "running" for e in REG["experiments"])}</span><span class="muted">Dashboard built {now}</span></div>

<div class="tiles">{tiles()}</div>

<div class="card"><h2>Conversion rate per traffic run</h2><p class="sub">Share of simulated sessions that purchased. One point per run; hover for details.</p>{cr_chart()}</div>

<div class="grid2">
<div class="card"><h2>Funnel: original vs current shop</h2><p class="sub">Share of all sessions reaching each step.</p>{funnel_chart()}</div>
<div class="card"><h2>How a cycle works</h2><p class="sub">Every step is run by Claude; traffic runs in GitHub Actions against the live site.</p>
<div class="pipe">
<div class="step"><b>Traffic</b>Simulated shoppers browse the live shop; events go to GA4 and our log.</div>
<div class="step"><b>Evaluate</b>Running tests checked against rules R1–R7: ship, stop or continue.</div>
<div class="step"><b>Analyse</b>Funnel, device, page and price-band cuts from the event log.</div>
<div class="step"><b>Hypothesise</b>Observation → hypothesis → change → metric, scored ICE.</div>
<div class="step"><b>Build &amp; QA</b>Variant coded behind a feature flag, rendered and checked.</div>
<div class="step"><b>Deploy</b>Commit → GitHub Pages; next traffic run queued.</div>
</div>
<h2 style="margin-top:18px">Timeline</h2><ul class="tline">{timeline_html()}</ul></div>
</div>

<div class="card"><h2>Experiments</h2><p class="sub">Primary-metric results per variant among exposed visitors. "Preview" opens the live shop in that variant (not tracked). Green = significant win at α = {RULES["alpha"]}.</p>
{experiments_html()}</div>

<div class="card"><h2>Hypothesis backlog</h2><p class="sub">What the engine plans to test next, ranked by ICE (Impact · Confidence · Ease).</p>
<div class="scroll"><table><thead><tr><th class="num">#</th><th>Observation</th><th>Change</th><th>Primary metric</th><th class="num">ICE</th><th>Status</th></tr></thead><tbody>{backlog_html()}</tbody></table></div></div>

<div class="grid2">
<div class="card"><h2>Decision rules</h2><p class="sub">Fixed in advance; the engine cannot ship a change that fails them.</p><div class="kvs">{rules_kv}</div><ol class="rules">{rules_list}</ol></div>
<div class="card"><h2>Shipped configuration</h2><p class="sub">Feature flags the live shop runs on. Highlighted rows differ from the original shop.</p>
<div class="scroll"><table><thead><tr><th>Flag</th><th>Now</th><th>Original</th><th>Changed by</th></tr></thead><tbody>{config_html()}</tbody></table></div></div>
</div>

<div class="card"><h2>Traffic runs</h2><p class="sub">Every batch of simulated shoppers. GA4 delivery = share of logged events that reached Google Analytics (audited runs only).</p>
<div class="scroll"><table><thead><tr><th>Run</th><th>Started</th><th>Type</th><th>Tests live</th><th class="num">Sessions</th><th class="num">Events</th><th class="num">Orders</th><th class="num">Conv.</th><th class="num">RPV</th><th class="num">GA4</th><th>Where</th></tr></thead>
<tbody>{runs_table()}</tbody></table></div></div>

<footer>Data: AutoCRO event log (source of truth) in the repo; GA4 property “AutoCRO – Fjeldspor” mirrors it. All shoppers and orders are simulated; Fjeldspor is fictional.
The simulator's hidden behaviour model is sealed from the analysis and from this dashboard.</footer>
</div></div><div id="tip" role="tooltip"></div>
<script>
(function(){{var t=document.getElementById('tip');document.querySelectorAll('.pt').forEach(function(g){{
g.addEventListener('mousemove',function(e){{t.innerHTML=g.dataset.tip.split('|').map(function(s,i){{return i?s:'<b>'+s+'</b>'}}).join('<br>');t.style.opacity=1;
var x=e.clientX+14,y=e.clientY+14;if(x+300>innerWidth)x=e.clientX-310;t.style.left=x+'px';t.style.top=y+'px'}});
g.addEventListener('mouseleave',function(){{t.style.opacity=0}})}})}})();
</script></body></html>'''

os.makedirs(os.path.join(ROOT, "dashboard/dist"), exist_ok=True)
out = os.path.join(ROOT, "dashboard/dist/autocro-dashboard.html")
open(out, "w").write(HTML)
os.makedirs(os.path.join(ROOT, "site/engine-room"), exist_ok=True)
open(os.path.join(ROOT, "site/engine-room/index.html"), "w").write(HTML.replace('<head>', '<head><meta name="robots" content="noindex">', 1))
print(out, len(HTML))
