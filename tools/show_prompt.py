#!/usr/bin/env python3
"""Print only what the model under test would see (the turns), for blind review.

  python3 tools/show_prompt.py ACB-04-001 [ACB-04-002 ...]
"""
import glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for i in sys.argv[1:]:
    p = glob.glob(os.path.join(ROOT, "items", "*", f"{i}.json"))
    if not p:
        print(f"== {i}: not found\n")
        continue
    d = json.load(open(p[0]))
    print(f"== {i} [{d['language']}]")
    for t in d["turns"]:
        print(f"--- {t['role']}:\n{t['content']}")
    print()
