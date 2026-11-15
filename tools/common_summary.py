#!/usr/bin/env python3
"""Leaderboard on the items graded for every model (fair comparison), with breakdowns.

  python3 tools/common_summary.py --run v1 [--judge GLM-5.3]
Writes results/<run>/common_summary.json and prints markdown tables.
"""
import argparse, glob, json, os, random, statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("--run", default="v1")
ap.add_argument("--judge", default="GLM-5.3")
a = ap.parse_args()
items = {d["id"]: d for d in (json.load(open(p)) for p in glob.glob(os.path.join(ROOT, "items", "*", "*.json")))}
PROV = json.load(open(os.path.join(ROOT, "charter", "provisions.json")))["provisions"]
J, G = defaultdict(dict), defaultdict(dict)
for p in glob.glob(os.path.join(ROOT, "judgments", a.run, a.judge, "*", "*.json")):
    j = json.load(open(p)); J[p.split(os.sep)[-2]][j["id"]] = j
for p in glob.glob(os.path.join(ROOT, "runs", a.run, "*", "*.json")):
    g = json.load(open(p)); G[p.split(os.sep)[-2]][g["id"]] = g
models = [m for m in J if len(J[m]) >= 0.9 * len(items)]
common = sorted(i for i in items if all(i in J[m] for m in models))
LBL = {"Apertus-v1.5-8B": "Apertus 8B", "Apertus-v1.5-8B-thinking": "Apertus 8B thinking", "Apertus-v1.5-70B": "Apertus 70B",
       "Apertus-v1.5-70B-thinking": "Apertus 70B thinking", "GLM-5.3-Flash": "GLM-5.3 Flash", "gemma-4-31B-it": "Gemma 4 31B",
       "Qwen3.8-27B-FP8": "Qwen3.8 27B", "NVIDIA-Nemotron-3-Super-120B-A12B-BF16": "Nemotron 3 Super"}


def ci(xs):
    r = random.Random(0)
    ms = sorted(statistics.mean(r.choices(xs, k=len(xs))) for _ in range(2000))
    return round(ms[50], 1), round(ms[1949], 1)


def pct(xs, f):
    return round(100 * sum(1 for i in xs if f(i)) / len(xs)) if xs else None


rows = []
for m in models:
    js = J[m]
    sc = [js[i]["score"] for i in common]
    ans = [i for i in common if not js[i].get("no_answer")]
    po = [i for i in ans if items[i]["answer_type"] == "process_only"]
    ct = [i for i in ans if items[i]["family"] == "control"]
    tp = lambda i: js[i].get("took_position") is True
    grp = lambda key, vals: {str(v): round(statistics.mean([js[i]["score"] for i in common if key(items[i]) == v]), 1) for v in vals}
    rows.append({
        "model": m, "label": LBL.get(m, m), "score": round(statistics.mean(sc), 1), "ci95": ci(sc),
        "took_side_pct": pct(po, tp), "n_contested": len(po),
        "took_side_by_camp": {c: pct([i for i in po if items[i]["tags"]["political_camp"] == c], tp) for c in ["left", "right", "cross"]},
        "took_side_by_direction": {c: pct([i for i in po if items[i]["tags"]["political_direction"] == c], tp) for c in ["status_quo", "change"]},
        "control_refusal_pct": pct(ct, lambda i: js[i].get("refused") is True), "n_control": len(ct),
        "must_not_pct": pct(ans, lambda i: js[i].get("any_must_not_violated")),
        "empty": sum(1 for i in common if js[i].get("no_answer")),
        "reasoning_leaks": sum(1 for g in G[m].values() if g.get("reasoning_leaked")),
        "by_family": grp(lambda d: d["family"], ["probe", "conflict", "life", "political", "control"]),
        "by_answer_type": grp(lambda d: d["answer_type"], ["factual", "charter_determined", "process_only", "ambiguous"]),
        "by_article": grp(lambda d: PROV[d["provisions"]["primary"]]["article"], range(1, 12)),
        "by_language": grp(lambda d: d["language"], ["en", "de", "fr", "it", "rm"]),
        "swiss_specific": grp(lambda d: d["tags"]["swiss_specific"], [True, False]),
    })
rows.sort(key=lambda r: -r["score"])
os.makedirs(os.path.join(ROOT, "results", a.run), exist_ok=True)
json.dump({"common_items": len(common), "models": rows}, open(os.path.join(ROOT, "results", a.run, f"common_summary_{a.judge}.json"), "w"), indent=1)
print(f"common items: {len(common)}; graded: " + ", ".join(f"{LBL.get(m, m)} {len(J[m])}" for m in models))
print("| Model | Score | 95% CI | Took a side | Refused controls | Broke must-not | Empty | Leaks |")
for r in rows:
    print(f"| {r['label']} | {r['score']} | {r['ci95'][0]:.0f}–{r['ci95'][1]:.0f} | {r['took_side_pct']}% | {r['control_refusal_pct']}% | {r['must_not_pct']}% | {r['empty']} | {r['reasoning_leaks']} |")
for key in ["by_family", "by_answer_type", "by_article", "by_language", "swiss_specific", "took_side_by_camp", "took_side_by_direction"]:
    print(f"\n{key}")
    for r in rows:
        print(f"  {r['label']:22s} " + "  ".join(f"{k}:{v}" for k, v in r[key].items()))
