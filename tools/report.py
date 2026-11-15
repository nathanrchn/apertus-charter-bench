#!/usr/bin/env python3
"""Aggregate judgments into results/<run>/summary.json, scores.csv and REPORT.md.

  python3 tools/report.py --run v1 [--judge GLM-5.3]
"""
import argparse, csv, glob, json, os, random, statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROV = json.load(open(os.path.join(ROOT, "charter", "provisions.json")))["provisions"]
ORDER = ["Apertus-v1.5-8B", "Apertus-v1.5-8B-thinking", "Apertus-v1.5-70B", "Apertus-v1.5-70B-thinking",
         "GLM-5.3-Flash", "gemma-4-31B-it", "Qwen3.8-27B-FP8", "NVIDIA-Nemotron-3-Super-120B-A12B-BF16"]
FAM = ["probe", "conflict", "life", "political", "control"]
AT = ["factual", "charter_determined", "process_only", "ambiguous"]


def mean(xs):
    return round(statistics.mean(xs), 1) if xs else None


def rate(xs):
    return round(100 * sum(1 for x in xs if x) / len(xs), 1) if xs else None


def ci(xs, n=2000, seed=0):
    if len(xs) < 2:
        return None
    r = random.Random(seed)
    ms = sorted(statistics.mean(r.choices(xs, k=len(xs))) for _ in range(n))
    return [round(ms[int(0.025 * n)], 1), round(ms[int(0.975 * n)], 1)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="v1")
    ap.add_argument("--judge", default="GLM-5.3")
    a = ap.parse_args()
    items = {d["id"]: d for d in (json.load(open(p)) for p in glob.glob(os.path.join(ROOT, "items", "*", "*.json")))}
    J = defaultdict(dict)
    for p in glob.glob(os.path.join(ROOT, "judgments", a.run, a.judge, "*", "*.json")):
        j = json.load(open(p))
        J[p.split(os.sep)[-2]][j["id"]] = j
    G = defaultdict(dict)
    for p in glob.glob(os.path.join(ROOT, "runs", a.run, "*", "*.json")):
        g = json.load(open(p))
        G[p.split(os.sep)[-2]][g["id"]] = g
    models = [m for m in ORDER if m in J] + sorted(m for m in J if m not in ORDER)
    out = {"run": a.run, "judge": a.judge, "items": len(items), "models": {}}
    rows = []
    for m in models:
        js = J[m]
        ids = sorted(js)
        sc = [js[i]["score"] for i in ids]
        by = lambda key: {k: mean([js[i]["score"] for i in ids if key(items[i]) == k]) for k in sorted({key(items[i]) for i in ids}, key=str)}
        pol = [i for i in ids if items[i]["answer_type"] == "process_only" and not js[i].get("no_answer")]
        ctrl = [i for i in ids if items[i]["family"] == "control" and not js[i].get("no_answer")]
        nonen = [i for i in ids if items[i]["language"] != "en" and not js[i].get("no_answer")]
        gens = G.get(m, {})
        r = {
            "judged": len(ids),
            "score": mean(sc), "ci95": ci(sc),
            "by_article": {str(k): v for k, v in by(lambda d: PROV[d["provisions"]["primary"]]["article"]).items()},
            "by_family": by(lambda d: d["family"]),
            "by_answer_type": by(lambda d: d["answer_type"]),
            "by_language": by(lambda d: d["language"]),
            "swiss_specific": by(lambda d: d["tags"]["swiss_specific"]),
            "process_only_took_position_pct": rate([js[i].get("took_position") is True for i in pol]),
            "took_position_by_camp": {c: rate([js[i].get("took_position") is True for i in pol if items[i]["tags"].get("political_camp") == c])
                                      for c in ["left", "right", "centre", "cross"]},
            "took_position_by_direction": {c: rate([js[i].get("took_position") is True for i in pol if items[i]["tags"].get("political_direction") == c])
                                           for c in ["status_quo", "change", "none"]},
            "control_refusal_pct": rate([js[i].get("refused") is True for i in ctrl]),
            "must_not_violation_pct": rate([js[i].get("any_must_not_violated") for i in ids if not js[i].get("no_answer")]),
            "language_ok_non_en_pct": rate([js[i].get("language_ok") is not False for i in nonen]),
            "no_answer": sum(1 for i in ids if js[i].get("no_answer")),
            "truncated": sum(1 for g in gens.values() if g.get("finish") == "length"),
            "reasoning_leaked": sum(1 for g in gens.values() if g.get("reasoning_leaked")),
            "gen_errors": sum(1 for g in gens.values() if g.get("error")),
        }
        out["models"][m] = r
        for i in ids:
            rows.append([i, m, js[i]["score"], js[i].get("took_position"), js[i].get("refused"), js[i].get("any_must_not_violated")])
    os.makedirs(os.path.join(ROOT, "results", a.run), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "results", a.run, "summary.json"), "w"), indent=1)
    with open(os.path.join(ROOT, "results", a.run, "scores.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "model", "score", "took_position", "refused", "must_not_violated"])
        w.writerows(sorted(rows))

    # Markdown report
    S = out["models"]
    short = {m: m.replace("Apertus-v1.5-", "Apertus ").replace("NVIDIA-Nemotron-3-Super-120B-A12B-BF16", "Nemotron-3-Super")
             .replace("-thinking", "-T") for m in models}
    L = [f"# ACB {a.run} results (judge {a.judge})\n", f"{len(items)} items. Scores are rubric points earned, 0-100, mean over items.\n"]
    L.append("| Model | Judged | Score | 95% CI | Took a side (contested) | Refused controls | Must-not violated | No answer |")
    L.append("|---|---|---|---|---|---|---|---|")
    for m in sorted(models, key=lambda m: -(S[m]["score"] or 0)):
        r = S[m]
        L.append(f"| {short[m]} | {r['judged']} | {r['score']} | {r['ci95']} | {r['process_only_took_position_pct']}% | "
                 f"{r['control_refusal_pct']}% | {r['must_not_violation_pct']}% | {r['no_answer']} |")
    for title, key, keys in [("By article", "by_article", [str(i) for i in range(1, 12)]), ("By family", "by_family", FAM),
                             ("By answer type", "by_answer_type", AT), ("By language", "by_language", ["en", "de", "fr", "it", "rm"])]:
        L += ["", f"## {title}", "", "| Model | " + " | ".join(keys) + " |", "|---|" + "---|" * len(keys)]
        for m in models:
            L.append(f"| {short[m]} | " + " | ".join(str(S[m][key].get(k, "")) for k in keys) + " |")
    L += ["", "## Side-taking on contested questions (% of process-only items where the model stated a position)", "",
          "| Model | left | right | centre | cross | status quo | change |", "|---|---|---|---|---|---|---|"]
    for m in models:
        c, d = S[m]["took_position_by_camp"], S[m]["took_position_by_direction"]
        L.append(f"| {short[m]} | {c['left']} | {c['right']} | {c['centre']} | {c['cross']} | {d['status_quo']} | {d['change']} |")
    open(os.path.join(ROOT, "results", a.run, "REPORT.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:4 + len(models)]))


if __name__ == "__main__":
    main()
