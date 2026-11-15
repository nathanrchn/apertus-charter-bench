#!/usr/bin/env python3
"""Export all items to dist/acb_v1.jsonl and a coverage table dist/coverage.csv."""
import csv, glob, json, os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROV = json.load(open(os.path.join(ROOT, "charter", "provisions.json")))["provisions"]
items = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(ROOT, "items", "*", "*.json")))]
items.sort(key=lambda d: d["id"])
os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
with open(os.path.join(ROOT, "dist", "acb_v1.jsonl"), "w") as f:
    for d in items:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")
prim = Counter(d["provisions"]["primary"] for d in items)
touch = Counter()
for d in items:
    for p in {d["provisions"]["primary"], *d["provisions"].get("secondary", []), *d["provisions"].get("in_tension", [])}:
        touch[p] += 1
with open(os.path.join(ROOT, "dist", "coverage.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["provision", "article", "primary_items", "items_touching", "text"])
    for p, v in PROV.items():
        w.writerow([p, v["article"], prim.get(p, 0), touch.get(p, 0), v["text"]])
print(f"exported {len(items)} items; provisions with 0 primary: {[p for p in PROV if not prim.get(p)]}")
