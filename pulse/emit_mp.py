#!/usr/bin/env python3
"""Send one day's event log to GA4 via Measurement Protocol (the site itself no longer tags).

Usage: python3 pulse/emit_mp.py data/events/D2026-11-11.jsonl [--dry]
Env:   MP_MEASUREMENT_ID, MP_API_SECRET
Events keep their simulated timestamps (must be < 72h old). Stdlib only.
"""
import gzip, json, os, sys, time, urllib.request
from collections import defaultdict

SKIP = {"session_start_ac"}                    # internal marker; GA4 makes its own session_start
PARAMS = ("currency", "value", "shipping", "transaction_id", "items", "page_type", "search_term",
          "item_list_name", "item_list_id")

def load(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as f:
        return [json.loads(l) for l in f if l.strip()]

def to_mp(e):
    p = {k: e[k] for k in PARAMS if k in e}
    for k, v in e.items():                     # keep any other simple custom params
        if k not in p and k not in ("run_id", "event", "ts", "ts_real", "client_id", "session_id", "device_category",
                                     "page_location", "experiments", "landing") and isinstance(v, (str, int, float)):
            p[k] = v
    p.update({"session_id": e["session_id"], "engagement_time_msec": 1500,
              "page_location": "https://crole-gregersen.github.io/autocro/" + e.get("page_location", "#/"),
              "ac_experiments": e.get("experiments", "")})
    return {"name": e["event"], "params": p, "timestamp_micros": int(e["ts"]) * 1000}

def main():
    path, dry = sys.argv[1], "--dry" in sys.argv
    mid, sec = os.environ.get("MP_MEASUREMENT_ID", ""), os.environ.get("MP_API_SECRET", "")
    url = f"https://www.google-analytics.com/mp/collect?measurement_id={mid}&api_secret={sec}"
    by_client = defaultdict(list)
    for e in load(path):
        if e["event"] not in SKIP:
            by_client[(e["client_id"], e.get("device_category", "desktop"))].append(e)
    limit = time.time() * 1000 - 71 * 3600e3
    sent = reqs = 0
    for (cid, dev), evs in by_client.items():
        evs.sort(key=lambda e: e["ts"])
        evs = [e for e in evs if e["ts"] > limit] if not dry else evs
        for i in range(0, len(evs), 25):       # MP max 25 events per request
            body = {"client_id": cid, "device": {"category": dev}, "events": [to_mp(e) for e in evs[i:i + 25]]}
            if not dry:
                urllib.request.urlopen(urllib.request.Request(url, json.dumps(body).encode(),
                                                              {"Content-Type": "application/json"}), timeout=20)
            sent += len(body["events"]); reqs += 1
    print(json.dumps({"file": path, "clients": len(by_client), "events_sent": sent, "requests": reqs, "dry": dry}))

if __name__ == "__main__":
    main()
