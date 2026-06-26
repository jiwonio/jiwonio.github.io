#!/usr/bin/env python3
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "lighthouse-report.json"
r = json.load(open(path, encoding="utf-8"))
print("Score:", int(r["categories"]["performance"]["score"] * 100))
for m in ("first-contentful-paint", "largest-contentful-paint", "total-blocking-time", "cumulative-layout-shift", "speed-index"):
    a = r["audits"][m]
    print(f"  {m}: {a['displayValue']} (score={a.get('score')})")
print("\nLow audits:")
for a in sorted(r["audits"].values(), key=lambda x: x.get("score") or 1):
    if a.get("score") is not None and a["score"] < 0.9:
        print(f"  {a['id']}: {a.get('displayValue','')} score={a['score']}")
print("\nRender blocking:")
rb = r["audits"].get("render-blocking-insight") or r["audits"].get("render-blocking-resources")
if rb and rb.get("details"):
    items = rb["details"].get("items", [])
    for item in items[:10]:
        print(f"  {item.get('url', item)}")