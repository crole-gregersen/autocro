#!/usr/bin/env python3
"""Pulse: turn a source GA4 property into anonymous, relative day factors for Fjeldspor.

Runs ONLY in GitHub Actions (secrets). Source numbers live in memory and are never written.
Output: data/pulse/<target-date>.json with factors around 1.0 (no levels, no source identity).

Env: SRC_SA_JSON (service-account key JSON), SRC_PROPERTY (GA4 property id),
     PULSE_SHIFT_WEEKS (int, secret), PULSE_SEED (secret), optional TARGET_DATE (YYYY-MM-DD).
Stdlib + openssl CLI only (no package installs).
"""
import base64, datetime as dt, json, os, random, subprocess, tempfile, time, urllib.request, urllib.parse
from collections import defaultdict

DAMP = 0.9        # how much of the source's day-to-day movement we keep (1.0 = all)
NOISE = 0.03      # extra multiplicative noise (sd)
WINDOW = 28       # reference window for "normal" level
CLIP = (0.3, 3.0)
METRICS = ["sessions", "addToCarts", "checkouts", "ecommercePurchases", "purchaseRevenue"]

def b64(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def token(sa):
    now = int(time.time())
    head = b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claim = b64(json.dumps({"iss": sa["client_email"], "aud": sa["token_uri"], "iat": now, "exp": now + 3600,
                            "scope": "https://www.googleapis.com/auth/analytics.readonly"}).encode())
    with tempfile.NamedTemporaryFile("w", delete=False) as k:
        k.write(sa["private_key"]); kp = k.name
    try:
        sig = subprocess.run(["openssl", "dgst", "-sha256", "-sign", kp], input=f"{head}.{claim}".encode(),
                             capture_output=True, check=True).stdout
    finally:
        os.unlink(kp)
    body = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                                   "assertion": f"{head}.{claim}.{b64(sig)}"}).encode()
    return json.load(urllib.request.urlopen(sa["token_uri"], body))["access_token"]

def report(tok, prop, start, end):
    req = {"dateRanges": [{"startDate": start, "endDate": end}],
           "dimensions": [{"name": "date"}, {"name": "hour"}, {"name": "deviceCategory"}],
           "metrics": [{"name": m} for m in METRICS], "limit": 100000}
    r = urllib.request.Request(f"https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport",
                               json.dumps(req).encode(), {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    out = defaultdict(lambda: {"m": defaultdict(float), "h": [0.0] * 24, "mob": 0.0})
    for row in json.load(urllib.request.urlopen(r)).get("rows", []):
        d, h, dev = (v["value"] for v in row["dimensionValues"])
        vals = [float(v["value"]) for v in row["metricValues"]]
        day = out[d]
        for m, v in zip(METRICS, vals): day["m"][m] += v
        day["h"][int(h)] += vals[0]
        if dev in ("mobile", "tablet"): day["mob"] += vals[0]
    return out

def rates(day):
    m = day["m"]; s = max(m["sessions"], 1)
    return {"traffic": m["sessions"],
            "mobile_share": day["mob"] / s,
            "atc_rate": m["addToCarts"] / s,
            "checkout_rate": m["checkouts"] / max(m["addToCarts"], 1),
            "purchase_rate": m["ecommercePurchases"] / max(m["checkouts"], 1),
            "aov": m["purchaseRevenue"] / max(m["ecommercePurchases"], 1)}

def factors(days, src_day, rng):
    keys = sorted(days)
    i = keys.index(src_day)
    ref = [rates(days[k]) for k in keys[max(0, i - WINDOW):i]]
    cur = rates(days[src_day])
    f = {}
    for k, v in cur.items():
        base = sum(r[k] for r in ref) / len(ref)
        raw = v / base if base else 1.0
        f[k] = round(min(max((1 + DAMP * (raw - 1)) * rng.gauss(1, NOISE), CLIP[0]), CLIP[1]), 3)
    tot = sum(days[src_day]["h"]) or 1
    shape = [x / tot for x in days[src_day]["h"]]
    shape = [max(0.0, s * rng.gauss(1, NOISE)) for s in shape]
    z = sum(shape) or 1
    return f, [round(s / z, 4) for s in shape]

def main():
    sa = json.loads(os.environ["SRC_SA_JSON"]); prop = os.environ["SRC_PROPERTY"]
    weeks = int(os.environ.get("PULSE_SHIFT_WEEKS", "3"))
    target = dt.date.fromisoformat(os.environ.get("TARGET_DATE") or str(dt.date.today() - dt.timedelta(days=1)))
    src = target - dt.timedelta(weeks=weeks)          # whole weeks keep the real weekday rhythm
    start = src - dt.timedelta(days=WINDOW)
    days = report(token(sa), prop, str(start), str(src))
    key = src.strftime("%Y%m%d")
    if key not in days or len(days) < WINDOW // 2:
        raise SystemExit("Not enough source data for this day")
    rng = random.Random(f"{os.environ.get('PULSE_SEED', '')}|{target}")
    f, shape = factors(days, key, rng)
    os.makedirs("data/pulse", exist_ok=True)
    with open(f"data/pulse/{target}.json", "w") as fh:
        json.dump({"date": str(target), "factors": f, "hour_shape": shape,
                   "_note": "Relative factors around 1.0; no source levels or identity."}, fh, indent=1)
    print(f"pulse {target}: " + ", ".join(f"{k}={v}" for k, v in f.items()))

if __name__ == "__main__":
    main()
