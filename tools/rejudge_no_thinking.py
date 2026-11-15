#!/usr/bin/env python3
"""Grade answers whose judgment is still missing (the judge reasoned past its token limit) with judge reasoning disabled.

  SWISSAI_RESEARCH_API_KEY=... python3 tools/rejudge_no_thinking.py --run v1
Judgments written this way carry "judge_mode": "no_thinking".
"""
import argparse, concurrent.futures as cf, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench

ap = argparse.ArgumentParser()
ap.add_argument("--run", default="v1")
a = ap.parse_args()
key = os.environ["SWISSAI_RESEARCH_API_KEY"]
items = {d["id"]: d for d in (json.load(open(p)) for p in glob.glob(os.path.join(bench.ROOT, "items", "*", "*.json")))}
jshort = bench.JUDGE.split("/")[-1]
todo = []
for p in glob.glob(os.path.join(bench.ROOT, "runs", a.run, "*", "*.json")):
    m = p.split(os.sep)[-2]
    out = os.path.join(bench.ROOT, "judgments", a.run, jshort, m, os.path.basename(p))
    if not os.path.exists(out):
        todo.append((p, out))
print(len(todo), "to grade", flush=True)
lim, health = bench.Limiter(14), bench.Health()


def work(t):
    p, out = t
    g = json.load(open(p))
    d = items[g["id"]]
    msgs = [{"role": "system", "content": bench.SYSTEM}, {"role": "user", "content": bench.judge_prompt(d, g["content"])}]
    for attempt in range(3):
        try:
            resp, secs = bench.post(bench.JUDGE, msgs, 8000, lim, health, key, temperature=0,
                                    extra={"chat_template_kwargs": {"enable_thinking": False}})
            j = bench.parse_judgment(resp["choices"][0]["message"].get("content") or "", d)
            j.update({"id": d["id"], "model": g["model"], "judge": bench.JUDGE, "judge_secs": secs, "attempts": attempt + 1,
                      "judge_mode": "no_thinking"})
            os.makedirs(os.path.dirname(out), exist_ok=True)
            json.dump(j, open(out, "w"), indent=1, ensure_ascii=False)
            return "ok"
        except Exception as e:
            err = repr(e)[:150]
    return f"failed {g['id']} {g['model']}: {err}"


with cf.ThreadPoolExecutor(6) as ex:
    for r in ex.map(work, todo):
        if r != "ok":
            print(r, flush=True)
print("done", flush=True)
