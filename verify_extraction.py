# -*- coding: utf-8 -*-
"""Verify extracted/images_extracted.json: numbering gaps, option completeness."""
import json
import re

data = json.load(open(r"extracted/images_extracted.json", encoding="utf-8"))
by_section = {}
for rec in data:
    by_section.setdefault(rec["section"], []).append(rec)

for si in sorted(by_section):
    recs = by_section[si]
    qnums = [r["question"] for r in recs]
    qset = sorted(set(qnums))
    lo, hi = min(qset), max(qset)
    missing = [n for n in range(lo, hi + 1) if n not in qset]
    dups = [n for n in qset if qnums.count(n) > 1]
    bad_opts = []
    for r in recs:
        letters = set(r["options"].keys())
        if letters != {"A", "B", "C", "D"}:
            bad_opts.append((r["question"], sorted(letters)))
    print(f"Section {si}: {len(recs)} records, qnums {lo}-{hi}, missing={missing}, dups={dups}")
    if bad_opts:
        print(f"   questions missing options: {bad_opts}")
    print()
