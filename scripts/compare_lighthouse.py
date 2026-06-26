#!/usr/bin/env python3
"""Print Lighthouse performance breakdown for diagnosis."""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "lighthouse-report.json"
r = json.load(open(path, encoding="utf-8"))
score = int(r["categories"]["performance"]["score"] * 100)
print(f"Performance: {score}%")
print()

metrics = [
    "first-contentful-paint",
    "largest-contentful-paint",
    "total-blocking-time",
    "cumulative-layout-shift",
    "speed-index",
    "interactive",
]
for name in metrics:
    a = r["audits"].get(name, {})
    if a.get("displayValue"):
        print(f"  {name}: {a['displayValue']} (score={a.get('score')})")

print("\nTop regressions / opportunities:")
for a in sorted(r["audits"].values(), key=lambda x: (x.get("score") is None, x.get("score") or 1)):
    if a.get("score") is not None and a["score"] < 0.75:
        print(f"  [{a['score']:.2f}] {a['id']}: {a.get('displayValue', '')}")

lcp = r["audits"].get("largest-contentful-paint-element", {})
for item in (lcp.get("details") or {}).get("items", []):
    if item.get("type") == "table" and item.get("headings"):
        rows = item.get("items", [])
        if rows and rows[0].get("phase"):
            print("\nLCP phases:")
            for row in rows:
                print(f"  {row['phase']}: {row.get('timing', 0):.0f}ms ({row.get('percent', '')})")
        elif rows and rows[0].get("node"):
            node = rows[0]["node"]
            print(f"\nLCP element: {node.get('selector')} ({node.get('nodeLabel', '')[:60]})")

cls = r["audits"].get("cls-culprits-insight", {})
for item in (cls.get("details") or {}).get("items", []):
    if item.get("type") == "table":
        for row in item.get("items", []):
            if row.get("subItems"):
                for sub in row["subItems"].get("items", []):
                    print(f"\nCLS cause: {sub.get('cause')} -> {sub.get('extra', {}).get('value', '')}")
            elif row.get("score") and row["score"] > 0.01:
                print(f"CLS shift: {row['score']:.4f} on {row.get('node', {}).get('selector', '')}")