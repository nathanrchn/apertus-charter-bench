#!/usr/bin/env python3
"""Validate ACB items and quota coverage.

Usage:
  python3 tools/lint.py --agent A4      # check one agent's batch against its assignment
  python3 tools/lint.py --all           # check everything + global coverage + duplicates
"""
import argparse, glob, json, os, re, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROV = json.load(open(os.path.join(ROOT, "charter", "provisions.json")))["provisions"]
FAMILIES = {"probe", "conflict", "life", "political", "control"}
ANSWER_TYPES = {"factual", "charter_determined", "process_only", "ambiguous"}
LANGS = {"en", "de", "fr", "it", "rm"}
CAMPS = {"left", "right", "centre", "cross"}
DIRECTIONS = {"status_quo", "change", "none"}
SENS = {"low", "medium", "high"}
DIFF = {"easy", "medium", "hard"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID = re.compile(r"^ACB-(\d{2})-(\d{3})$")
REQUIRED = ["id", "title", "family", "charter_version", "provisions", "language", "turns", "rationale",
            "provenance", "research_brief", "answer_type", "expected_behavior", "reference_answer",
            "must_include", "must_not", "rubric", "key_facts", "interpretation_note", "readings", "tags",
            "difficulty", "review"]
TAGS = ["swiss_specific", "sensitivity", "multi_turn", "pressure", "time_sensitive", "as_of",
        "political_camp", "political_direction", "mirror_of", "twin_of"]


def words(s):
    return len(re.findall(r"\w+", s or ""))


def check_item(path, d, errs):
    e = lambda m: errs.append(f"{os.path.relpath(path, ROOT)}: {m}")
    for k in REQUIRED:
        if k not in d:
            e(f"missing key '{k}'")
    if any(k not in d for k in ("id", "provisions", "turns", "tags", "provenance")):
        return
    m = ID.match(d["id"])
    if not m:
        e(f"bad id {d['id']}")
    elif os.path.basename(path) != d["id"] + ".json":
        e("filename must be <id>.json")
    pr = d["provisions"].get("primary")
    if pr not in PROV:
        e(f"primary provision '{pr}' does not exist")
    elif m and int(m.group(1)) != PROV[pr]["article"]:
        e(f"id article {m.group(1)} != primary provision article {PROV[pr]['article']}")
    for key in ("secondary", "in_tension"):
        v = d["provisions"].get(key, [])
        if not isinstance(v, list):
            e(f"provisions.{key} must be a list")
            continue
        for p in v:
            if p not in PROV:
                e(f"provisions.{key}: '{p}' does not exist")
    if d.get("family") not in FAMILIES:
        e(f"family '{d.get('family')}' invalid")
    if d.get("family") == "conflict" and not d["provisions"].get("in_tension"):
        e("conflict items need provisions.in_tension")
    if d.get("answer_type") not in ANSWER_TYPES:
        e(f"answer_type '{d.get('answer_type')}' invalid")
    if d.get("language") not in LANGS:
        e(f"language '{d.get('language')}' invalid")
    t = d["turns"]
    if not isinstance(t, list) or not t:
        e("turns must be a non-empty list")
    else:
        for i, turn in enumerate(t):
            want = "user" if i % 2 == 0 else "assistant"
            if turn.get("role") != want or not (turn.get("content") or "").strip():
                e(f"turn {i} must be role={want} with content")
        if t[-1].get("role") != "user":
            e("last turn must be user")
        users = sum(1 for x in t if x.get("role") == "user")
        if bool(d["tags"].get("multi_turn")) != (users > 1):
            e("tags.multi_turn must be true iff there is more than one user turn")
    pv = d["provenance"]
    if not pv.get("types") or not isinstance(pv.get("types"), list):
        e("provenance.types must be a non-empty list")
    if words(pv.get("summary")) < 8:
        e("provenance.summary too short")
    src = pv.get("sources") or []
    need = 2 if d.get("answer_type") == "factual" else 1
    if len(src) < need:
        e(f"needs >= {need} sources")
    for i, s in enumerate(src):
        for k in ("title", "url", "publisher", "accessed", "supports", "quote"):
            if not (s.get(k) or "").strip():
                e(f"source {i} missing '{k}'")
        if not str(s.get("url", "")).startswith("http"):
            e(f"source {i} url must start with http")
        if s.get("accessed") and not DATE.match(s["accessed"]):
            e(f"source {i} accessed must be YYYY-MM-DD")
        if words(s.get("quote")) > 60:
            e(f"source {i} quote longer than 60 words")
    rb = d.get("research_brief") or ""
    if not rb or not os.path.exists(os.path.join(ROOT, rb)):
        e(f"research_brief '{rb}' does not exist")
    if words(d.get("rationale")) < 10:
        e("rationale too short")
    if words(d.get("expected_behavior")) < 15:
        e("expected_behavior too short")
    rw = words(d.get("reference_answer"))
    if rw < 40 or rw > 450:
        e(f"reference_answer has {rw} words (want 40-450)")
    for k in ("must_include", "must_not"):
        v = d.get(k)
        if not isinstance(v, list) or not (1 <= len(v) <= 7):
            e(f"{k} must be a list of 1-7 items")
    rub = d.get("rubric") or []
    if not (3 <= len(rub) <= 6):
        e("rubric must have 3-6 criteria")
    for i, r in enumerate(rub):
        if not r.get("criterion") or r.get("weight") not in (1, 2, 3) or not r.get("provisions"):
            e(f"rubric {i} needs criterion, provisions, weight 1-3")
        for p in r.get("provisions", []):
            if p not in PROV:
                e(f"rubric {i}: provision '{p}' does not exist")
    kf = d.get("key_facts")
    if not isinstance(kf, list):
        e("key_facts must be a list")
    else:
        if d.get("answer_type") == "factual" and not kf:
            e("factual items need key_facts")
        for i, k in enumerate(kf):
            if not k.get("claim") or not isinstance(k.get("source_index"), int) or not (0 <= k["source_index"] < len(src)):
                e(f"key_fact {i} needs claim and a valid source_index")
    if d.get("answer_type") == "ambiguous":
        if words(d.get("interpretation_note")) < 10:
            e("ambiguous items need interpretation_note")
        if not isinstance(d.get("readings"), list) or len(d["readings"]) < 2:
            e("ambiguous items need >= 2 readings")
    tg = d["tags"]
    for k in TAGS:
        if k not in tg:
            e(f"tags.{k} missing")
    if not isinstance(tg.get("swiss_specific"), bool):
        e("tags.swiss_specific must be bool")
    if tg.get("sensitivity") not in SENS:
        e("tags.sensitivity must be low/medium/high")
    if tg.get("time_sensitive") and not (tg.get("as_of") and DATE.match(str(tg["as_of"]))):
        e("time_sensitive items need tags.as_of YYYY-MM-DD")
    if d.get("family") == "political":
        if tg.get("political_camp") not in CAMPS:
            e("political items need tags.political_camp")
        if tg.get("political_direction") not in DIRECTIONS:
            e("political items need tags.political_direction")
    if d.get("difficulty") not in DIFF:
        e("difficulty must be easy/medium/hard")
    if not (d.get("review") or {}).get("drafted_by"):
        e("review.drafted_by missing")


def load(paths, errs):
    items = {}
    for p in sorted(paths):
        try:
            d = json.load(open(p))
        except Exception as ex:
            errs.append(f"{os.path.relpath(p, ROOT)}: invalid JSON: {ex}")
            continue
        if not isinstance(d, dict):
            errs.append(f"{os.path.relpath(p, ROOT)}: top level must be a JSON object")
            continue
        try:
            check_item(p, d, errs)
        except Exception as ex:  # malformed field types must not crash other agents' runs
            errs.append(f"{os.path.relpath(p, ROOT)}: malformed item ({type(ex).__name__}: {ex}); compare with docs/example_item.json")
        if d.get("id") in items:
            errs.append(f"duplicate id {d.get('id')}")
        items[d.get("id")] = d
    return items


def refs(items, all_ids, errs):
    for i, d in items.items():
        tg = d.get("tags", {})
        for k in ("twin_of", "mirror_of"):
            v = tg.get(k)
            if v and v not in all_ids:
                errs.append(f"{i}: tags.{k} -> unknown id {v}")


def quota(spec, items, errs):
    a = spec["agent"]
    for art, s in spec["per_article"].items():
        sub = [d for d in items.values() if d.get("provisions", {}).get("primary", "").split(".")[0] == art]
        got = Counter(d["provisions"]["primary"] for d in sub)
        for p, n in s["provision_counts"].items():
            if got.get(p, 0) != n:
                errs.append(f"[{a}] article {art}: provision {p} has {got.get(p, 0)} items, want {n}")
        fam = Counter(d.get("family") for d in sub)
        for f, n in s["family_counts"].items():
            if fam.get(f, 0) != n:
                errs.append(f"[{a}] article {art}: family {f} has {fam.get(f, 0)}, want {n}")
    lang = Counter(d.get("language") for d in items.values())
    for l, n in spec["language_counts"].items():
        if lang.get(l, 0) != n:
            errs.append(f"[{a}] language {l} has {lang.get(l, 0)}, want {n}")
    sw = sum(1 for d in items.values() if d.get("tags", {}).get("swiss_specific") is True)
    if sw < spec["min_swiss_specific"]:
        errs.append(f"[{a}] swiss_specific {sw}, want >= {spec['min_swiss_specific']}")
    mt = sum(1 for d in items.values() if d.get("tags", {}).get("multi_turn") is True)
    if mt != spec["multi_turn_count"]:
        errs.append(f"[{a}] multi_turn {mt}, want {spec['multi_turn_count']}")
    tw = sum(1 for d in items.values() if d.get("tags", {}).get("twin_of"))
    if tw != spec["twin_count"]:
        errs.append(f"[{a}] twins {tw}, want {spec['twin_count']}")
    if len(items) != spec["total_items"]:
        errs.append(f"[{a}] {len(items)} items, want {spec['total_items']}")
    if a == "A7":
        pairs = sum(1 for d in items.values() if d.get("tags", {}).get("mirror_of"))
        if pairs < 6:
            errs.append(f"[A7] mirrored political items {pairs}, want >= 6")


def shingles(s, n=4):
    w = re.findall(r"\w+", s.lower())
    return {" ".join(w[i:i + n]) for i in range(max(1, len(w) - n + 1))}


def dupes(items, warns):
    sh = {i: shingles(" ".join(t["content"] for t in d.get("turns", []))) for i, d in items.items()}
    ids = sorted(sh)
    for x in range(len(ids)):
        for y in range(x + 1, len(ids)):
            a, b = sh[ids[x]], sh[ids[y]]
            j = len(a & b) / max(1, len(a | b))
            tw = {items[ids[x]]["tags"].get("twin_of"), items[ids[y]]["tags"].get("twin_of")}
            if j > 0.35 and ids[x] not in tw and ids[y] not in tw:
                warns.append(f"near-duplicate prompts {ids[x]} ~ {ids[y]} (jaccard {j:.2f})")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--agent")
    g.add_argument("--all", action="store_true")
    args = ap.parse_args()
    errs, warns = [], []
    all_items = load(glob.glob(os.path.join(ROOT, "items", "*", "*.json")), [])
    if args.agent:
        spec = json.load(open(os.path.join(ROOT, "assignments", args.agent + ".json")))
        items = load(glob.glob(os.path.join(ROOT, spec["items_dir"], "*.json")), errs)
        refs(items, set(all_items), errs)
        quota(spec, items, errs)
        dupes(items, warns)
    else:
        items = load(glob.glob(os.path.join(ROOT, "items", "*", "*.json")), errs)
        refs(items, set(items), errs)
        for f in sorted(glob.glob(os.path.join(ROOT, "assignments", "*.json"))):
            spec = json.load(open(f))
            sub = {i: d for i, d in items.items()
                   if os.path.exists(os.path.join(ROOT, spec["items_dir"], f"{i}.json"))}
            quota(spec, sub, errs)
        dupes(items, warns)
        print(f"items: {len(items)}")
        print("families:", dict(Counter(d.get("family") for d in items.values())))
        print("answer_types:", dict(Counter(d.get("answer_type") for d in items.values())))
        print("languages:", dict(Counter(d.get("language") for d in items.values())))
        cov = Counter(d.get("provisions", {}).get("primary") for d in items.values())
        missing = [p for p in PROV if cov.get(p, 0) < 2]
        print("provisions with < 2 primary items:", missing or "none")
    for w in warns:
        print("WARN", w)
    for x in errs:
        print("ERROR", x)
    print(f"{len(errs)} errors, {len(warns)} warnings")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
