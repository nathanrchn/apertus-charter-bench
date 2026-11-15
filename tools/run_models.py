#!/usr/bin/env python3
"""Send every ACB item to the Apertus models on the Swiss AI API (resumable).

  SWISSAI_RESEARCH_API_KEY=... python3 tools/run_models.py --run pilot1 [--samples 3] [--ids ACB-04-001,...]

Outputs: runs/<run>/<model-short>/<item-id>__s<k>.json
Notes (from the 2026-11 pilot):
  - macOS python needs SSL_CERT_FILE=/etc/ssl/cert.pem (set automatically below if unset)
  - >3 concurrent requests -> HTTP 429; we use 3 + exponential backoff
  - 70B-thinking leaks <|inner_prefix|>...<|inner_suffix|> into content; we split it into `reasoning`
"""
import argparse, concurrent.futures as cf, glob, json, os, threading, time, urllib.error, urllib.request

os.environ.setdefault("SSL_CERT_FILE", "/etc/ssl/cert.pem")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.swissai.svc.cscs.ch/v1/chat/completions"
MODELS = [
    "CSCS-Inference/swiss-ai/Apertus-v1.5-8B",
    "CSCS-Inference/swiss-ai/Apertus-v1.5-8B-thinking",
    "CSCS-Inference/swiss-ai/Apertus-v1.5-70B",
    "CSCS-Inference/swiss-ai/Apertus-v1.5-70B-thinking",
]


def split_leak(content):
    c = content or ""
    if "<|inner_prefix|>" not in c:
        return c, None
    if "<|inner_suffix|>" in c:
        r, f = c.split("<|inner_suffix|>", 1)
        return f.strip(), r.replace("<|inner_prefix|>", "").strip()
    return "", c.replace("<|inner_prefix|>", "").strip()


def call(model, messages, key, max_tokens):
    body = {"model": model, "messages": messages, "max_tokens": max_tokens}
    req = urllib.request.Request(API, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    err = None
    for attempt in range(8):
        try:
            t = time.time()
            with urllib.request.urlopen(req, timeout=900) as r:
                d = json.load(r)
            c = d["choices"][0]
            content, leaked = split_leak(c["message"].get("content"))
            return {"content": content, "reasoning": c["message"].get("reasoning") or leaked,
                    "reasoning_leaked": leaked is not None, "finish": c.get("finish_reason"),
                    "usage": d.get("usage"), "secs": round(time.time() - t, 1)}
        except urllib.error.HTTPError as e:
            err = repr(e)
            ra = e.headers.get("Retry-After") if e.headers else None
            time.sleep(float(ra) if ra and ra.replace(".", "", 1).isdigit() else min(120, 10 * 2 ** attempt))
        except Exception as e:
            err = repr(e)
            time.sleep(10)
    return {"error": err}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--samples", type=int, default=1)
    ap.add_argument("--ids", default="")
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--conc", type=int, default=3)
    args = ap.parse_args()
    key = os.environ["SWISSAI_RESEARCH_API_KEY"]
    items = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(ROOT, "items", "*", "*.json")))]
    if args.ids:
        keep = set(args.ids.split(","))
        items = [d for d in items if d["id"] in keep]
    jobs = []
    for d in items:
        for m in args.models.split(","):
            for s in range(args.samples):
                out = os.path.join(ROOT, "runs", args.run, m.split("/")[-1], f"{d['id']}__s{s}.json")
                if os.path.exists(out) and json.load(open(out)).get("content") is not None:
                    continue
                jobs.append((d, m, s, out))
    print(f"{len(items)} items, {len(jobs)} calls to make", flush=True)
    lock = threading.Lock()
    done = [0]

    def work(job):
        d, m, s, out = job
        mt = 16000 if "thinking" in m else 4000
        r = call(m, [{"role": t["role"], "content": t["content"]} for t in d["turns"]], key, mt)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump({"id": d["id"], "model": m, "sample": s, **r}, open(out, "w"), indent=1, ensure_ascii=False)
        with lock:
            done[0] += 1
            if done[0] % 25 == 0 or "error" in r:
                print(done[0], d["id"], m.split("/")[-1], r.get("finish") or r.get("error"), flush=True)

    with cf.ThreadPoolExecutor(args.conc) as ex:
        list(ex.map(work, jobs))
    print("done", flush=True)


if __name__ == "__main__":
    main()
