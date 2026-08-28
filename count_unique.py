# -*- coding: utf-8 -*-
"""Count unique questions across all sources (MCQ stems + essay prompts)."""
import json
import os
import re

ROOT = r"c:\Users\jason\Documents\mycat"
WS = os.path.join(ROOT, "workspace")


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def load_handwritten():
    p = os.path.join(ROOT, "site", "questions.js")
    text = open(p, encoding="utf-8").read()
    # The hand-written file uses JS object syntax (unquoted keys), so count
    # questions by the "question:" key rather than JSON-parsing.
    n = len(re.findall(r"\bquestion\s*:", text))
    return [{"id": f"hand-{i}", "question": f"handwritten question {i}"} for i in range(n)]


mcqs = []
mcqs += load_handwritten()
mcqs += load_jsonl(os.path.join(WS, "generated_full_fig.jsonl"))
mcqs += load_jsonl(os.path.join(WS, "generated_hard_demo.jsonl"))
mcqs += load_jsonl(os.path.join(WS, "generated_scenario.jsonl"))
mcqs += load_jsonl(os.path.join(WS, "generated_topup.jsonl"))
essays = load_jsonl(os.path.join(WS, "generated_essay.jsonl"))

stems = {}
for q in mcqs:
    if not q.get("question"):
        continue
    s = norm(q["question"])
    stems.setdefault(s, []).append(q.get("id", "?"))

dupes = {s: ids for s, ids in stems.items() if len(ids) > 1}
eprompts = {}
for e in essays:
    p = norm(e.get("prompt", ""))
    if p:
        eprompts.setdefault(p, []).append(e.get("id", "?"))

out = [
    f"MCQ total: {len(mcqs)}",
    f"MCQ unique stems: {len(stems)}",
    f"MCQ duplicate stems: {len(dupes)}",
    f"Essay total: {len(essays)}",
    f"Essay unique prompts: {len(eprompts)}",
    f"GRAND unique (MCQ stems + essay prompts): {len(stems) + len(eprompts)}",
]
open(os.path.join(ROOT, "count_report.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
