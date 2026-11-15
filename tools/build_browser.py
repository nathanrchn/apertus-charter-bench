#!/usr/bin/env python3
"""Build a single-file HTML browser for all ACB items, with model answers and judge scores when available.

  python3 tools/build_browser.py [out.html] [--run v1] [--judge GLM-5.3]   (default out: dist/browser.html)
"""
import argparse, datetime, glob, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = ["Apertus-v1.5-8B", "Apertus-v1.5-8B-thinking", "Apertus-v1.5-70B", "Apertus-v1.5-70B-thinking",
         "GLM-5.3-Flash", "gemma-4-31B-it", "Qwen3.8-27B-FP8", "NVIDIA-Nemotron-3-Super-120B-A12B-BF16"]
LABEL = {"Apertus-v1.5-8B": "Apertus 8B", "Apertus-v1.5-8B-thinking": "Apertus 8B thinking", "Apertus-v1.5-70B": "Apertus 70B",
         "Apertus-v1.5-70B-thinking": "Apertus 70B thinking", "GLM-5.3-Flash": "GLM-5.3 Flash", "gemma-4-31B-it": "Gemma 4 31B",
         "Qwen3.8-27B-FP8": "Qwen3.8 27B", "NVIDIA-Nemotron-3-Super-120B-A12B-BF16": "Nemotron 3 Super"}


def embed(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


JLABEL = {"GLM-5.3": "GLM-5.3", "Qwen3.8-27B-FP8": "Qwen3.8 27B", "mean": "Mean of judges"}


def judge_entry(j):
    e = {"s": j.get("score")}
    if j.get("no_answer"):
        e["na"] = True
    if "criteria" in j:
        e.update({"c": [c.get("score") for c in j["criteria"]], "r": [c.get("reason", "") for c in j["criteria"]],
                  "tp": j.get("took_position"), "pos": j.get("position"), "ref": j.get("refused"),
                  "mi": j.get("must_include_met"), "mn": j.get("must_not_violated"), "fe": j.get("factual_errors") or [],
                  "sm": j.get("summary"), "lang": j.get("language_ok"), "nothink": j.get("judge_mode") == "no_thinking"})
    return e


def results(run, judges):
    by, models = {}, []
    for gdir in sorted(glob.glob(os.path.join(ROOT, "runs", run, "*"))):
        if not os.path.isdir(gdir):
            continue
        m = os.path.basename(gdir)
        models.append(m)
        for p in glob.glob(os.path.join(gdir, "*.json")):
            g = json.load(open(p))
            if g.get("error"):
                continue
            e = {"a": g.get("content") or "", "fin": g.get("finish"), "leak": bool(g.get("reasoning_leaked")),
                 "rl": len(g.get("reasoning") or ""), "J": {}}
            for jd in judges:
                jp = os.path.join(ROOT, "judgments", run, jd, m, os.path.basename(p))
                if os.path.exists(jp):
                    e["J"][jd] = judge_entry(json.load(open(jp)))
            js = [e["J"][jd] for jd in judges if e["J"].get(jd, {}).get("s") is not None]
            if len(judges) > 1 and len(js) == len(judges):
                avg = lambda xs: sum(xs) / len(xs)
                frac = lambda k: avg([1.0 if x.get(k) is True else 0.0 for x in js])
                anymn = lambda x: any(v is True for v in (x.get("mn") or []))
                e["J"]["mean"] = {"s": round(avg([x["s"] for x in js]), 1), "na": all(x.get("na") for x in js) or None,
                                  "tpf": frac("tp"), "reff": frac("ref"), "mnf": avg([1.0 if anymn(x) else 0.0 for x in js]),
                                  "sm": "Mean of " + " and ".join(JLABEL.get(j, j) for j in judges) + ". Switch judge to see the criterion-level grading."}
            by.setdefault(g["id"], {})[m] = e
    keys = judges + (["mean"] if len(judges) > 1 else [])
    graded_n = {m: max(sum(1 for v in by.values() if v.get(m, {}).get("J", {}).get(jd, {}).get("s") is not None) for jd in judges) for m in models}
    models = [m for m in models if graded_n[m] >= 0.9 * len(by)]  # show a model once it is (almost) fully graded
    by = {i: {m: e for m, e in v.items() if m in models} for i, v in by.items()}
    models = [m for m in ORDER if m in models] + [m for m in models if m not in ORDER]
    return {"run": run, "judges": [{"key": k, "label": JLABEL.get(k, k)} for k in keys],
            "default_judge": "mean" if len(judges) > 1 else judges[0],
            "updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "models": [{"key": m, "label": LABEL.get(m, m)} for m in models], "by_item": by}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default=os.path.join(ROOT, "dist", "browser.html"))
    ap.add_argument("--run", default="v1")
    ap.add_argument("--judges", default="", help="comma list; default: every judge directory under judgments/<run>")
    a = ap.parse_args()
    items = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(ROOT, "items", "*", "*.json")))]
    ch = json.load(open(os.path.join(ROOT, "charter", "provisions.json")))
    ch["built"] = datetime.date.today().isoformat()
    txt = open(os.path.join(ROOT, "charter", "charter_v1.0.txt")).read()
    if "Preamble" in txt:
        pre = txt.split("Preamble", 1)[1].strip().split("\n\n")[0].strip()
        ch["preamble"] = pre
    jds = a.judges.split(",") if a.judges else sorted(os.path.basename(x) for x in glob.glob(os.path.join(ROOT, "judgments", a.run, "*")))
    res = results(a.run, jds) if os.path.isdir(os.path.join(ROOT, "runs", a.run)) else {}
    tpl = open(os.path.join(ROOT, "tools", "browser_template.html")).read()
    html = tpl.replace("__DATA__", embed(items)).replace("__PROV__", embed(ch)).replace("__RESULTS__", embed(res))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w").write(html)
    n = sum(1 for v in res.get("by_item", {}).values() for e in v.values() for k, x in e["J"].items() if k != "mean" and x.get("s") is not None)
    print(f"{a.out}: {len(items)} items, {n} graded answers, {len(html.encode()) / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
