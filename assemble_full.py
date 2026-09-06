# -*- coding: utf-8 -*-
"""Assemble the full-length exam: longform passages (majority) + discrete (minority).

Reads workspace/generated_passage.jsonl and workspace/generated_discrete.jsonl,
merges them, verifies that passage questions are the majority, and writes
workspace/generated_full.jsonl (+ .json) in section order.
"""
import json
import os
from collections import Counter

WS = r"c:\Users\jason\Documents\mycat\workspace"
PASSAGE_IN = os.path.join(WS, "generated_passage.jsonl")
DISCRETE_IN = os.path.join(WS, "generated_discrete.jsonl")
OUT = os.path.join(WS, "generated_full.jsonl")

SECTION_ORDER = [
    "Chemical & Physical Foundations",
    "Biological & Biochemical Foundations",
    "Psychological, Social, & Biological Foundations",
    "Critical Analysis and Reasoning Skills",
]


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def main():
    passages = load_jsonl(PASSAGE_IN)
    discrete = load_jsonl(DISCRETE_IN)
    merged = passages + discrete

    # stable ordering: section order, then id
    def rank(q):
        try:
            si = SECTION_ORDER.index(q.get("section"))
        except ValueError:
            si = len(SECTION_ORDER)
        return (si, q.get("id", ""))

    merged.sort(key=rank)

    n_passage = sum(1 for q in merged if q.get("type") == "passage")
    n_discrete = sum(1 for q in merged if q.get("type") == "discrete")
    print(f"passage questions: {n_passage}")
    print(f"discrete questions: {n_discrete}")
    print(f"total: {len(merged)}")
    if not (n_passage > n_discrete):
        raise SystemExit("FAIL: passage questions are not the majority")

    with open(OUT, "w", encoding="utf-8") as f:
        for q in merged:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    with open(OUT.replace(".jsonl", ".json"), "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print("sections:", dict(Counter(q.get("section") for q in merged)))
    print(f"WROTE {OUT}")


if __name__ == "__main__":
    main()
