#!/usr/bin/env python3
"""Per-provision (charter point) scores for every model, from rubric-criterion scores of both judges.

  python3 tools/provision_breakdown.py --run v1
Criterion score: each rubric criterion lists the provisions it tests; its 0-2 score (mean over judges) maps to 0-100
and counts toward every provision it lists. Also reports the mean item score on items whose primary provision it is.
Writes results/<run>/provision_breakdown.json and .csv.
"""
import argparse, csv, glob, json, os, statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("--run", default="v1")
ap.add_argument("--min-n", type=int, default=4)
a = ap.parse_args()
PROV = json.load(open(os.path.join(ROOT, "charter", "provisions.json")))["provisions"]
items = {d["id"]: d for d in (json.load(open(p)) for p in glob.glob(os.path.join(ROOT, "items", "*", "*.json")))}
judges = sorted(os.path.basename(x) for x in glob.glob(os.path.join(ROOT, "judgments", a.run, "*")))
J = {jd: defaultdict(dict) for jd in judges}
for jd in judges:
    for p in glob.glob(os.path.join(ROOT, "judgments", a.run, jd, "*", "*.json")):
        x = json.load(open(p)); J[jd][p.split(os.sep)[-2]][x["id"]] = x
models = sorted(set().union(*[set(J[jd]) for jd in judges]))
crit = defaultdict(lambda: defaultdict(list))      # model -> provision -> [(score0-100, item, criterion)]
prim = defaultdict(lambda: defaultdict(list))      # model -> provision -> [item score]
for m in models:
    for iid, d in items.items():
        js = [J[jd][m][iid] for jd in judges if iid in J[jd][m]]
        if not js:
            continue
        prim[m][d["provisions"]["primary"]].append(statistics.mean(x["score"] for x in js))
        for k, r in enumerate(d["rubric"]):
            ss = [x["criteria"][k]["score"] for x in js if x.get("criteria") and len(x["criteria"]) == len(d["rubric"])]
            if not ss and all(x.get("no_answer") for x in js):
                ss = [0]
            if ss:
                for p in r.get("provisions", []):
                    crit[m][p].append((50 * statistics.mean(ss), iid, r["criterion"]))
out = {"judges": judges, "models": {}}
field = {p: statistics.mean(s for m in models for s, _, _ in crit[m][p]) for p in PROV if any(crit[m][p] for m in models)}
rows = []
for m in models:
    pm = {}
    for p in PROV:
        xs = crit[m][p]
        if not xs:
            continue
        sc = statistics.mean(s for s, _, _ in xs)
        worst = sorted(xs)[:3]
        pm[p] = {"criterion_score": round(sc, 1), "n_criteria": len(xs), "vs_field": round(sc - field[p], 1),
                 "primary_item_score": round(statistics.mean(prim[m][p]), 1) if prim[m][p] else None, "n_primary_items": len(prim[m][p]),
                 "worst": [{"item": i, "criterion": c, "score": round(s)} for s, i, c in worst]}
        rows.append([m, p, PROV[p]["article"], round(sc, 1), len(xs), round(sc - field[p], 1), pm[p]["primary_item_score"], len(prim[m][p])])
    out["models"][m] = pm
out["field_mean"] = {p: round(v, 1) for p, v in field.items()}
json.dump(out, open(os.path.join(ROOT, "results", a.run, "provision_breakdown.json"), "w"), indent=1)
with open(os.path.join(ROOT, "results", a.run, "provision_breakdown.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["model", "provision", "article", "criterion_score", "n_criteria", "vs_field", "primary_item_score", "n_primary_items"]); w.writerows(rows)
print(f"judges {judges}; provisions covered {len(field)}/{len(PROV)}")
