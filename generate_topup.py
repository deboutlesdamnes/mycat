# -*- coding: utf-8 -*-
"""Generate an additional batch of MCQs to push the bank past 1000 unique
questions. Reuses the full-length prompt + skill map; writes to
workspace/generated_topup.jsonl.
"""
import json
import os
import zlib
from collections import Counter

from deepseek_backend import chat
from gen_config import build_tasks
from generate_questions_llm import SYSTEM_PROMPT, skill_for

OUT_DIR = r"c:\Users\jason\Documents\mycat\workspace"
PER_TOPIC = 6


def build_user(t):
    if t["cars"]:
        return (
            f"Write {PER_TOPIC} CARS passage-based questions on the theme: {t['topic']}. "
            f"Provide ONE shared passage in the 'passage' field of every question. Cover a mix "
            f"of CARS skills (subtypes: main-idea, detail, function, def-context, inference, "
            f"strengthen-weaken, apply). Assign each a difficulty (easy/medium/hard). "
            f"Vary the question phrasings. Return JSON."
        )
    return (
        f"Subject: {t['subject']}. Topic: {t['topic']}. Write {PER_TOPIC} questions. "
        f"Vary the subtypes among: recall, except, vignette, data-interp, passage, compare, "
        f"sequence, predict, yes-no. For data-interp and passage questions put the data/passage "
        f"in the 'passage' field. Assign each a difficulty (easy/medium/hard). "
        f"Vary the question phrasings. Return JSON."
    )


def normalize(q, t, idx):
    if not isinstance(q, dict):
        return None
    opts = q.get("options")
    if not isinstance(opts, list) or len(opts) != 4 or not q.get("question"):
        return None
    try:
        correct = int(q.get("correct"))
    except (TypeError, ValueError):
        return None
    if not (0 <= correct <= 3):
        return None

    difficulty = q.get("difficulty")
    if difficulty not in ("easy", "medium", "hard"):
        difficulty = "medium"
    subtype = q.get("subtype") or ("passage" if q.get("passage") else "recall")

    out = dict(q)
    out["id"] = f"topup-{idx:03d}"
    out["section"] = t["section"]
    out["subject"] = t["subject"]
    out["topic"] = t["topic"]
    out["knowledge_point"] = t["topic"]
    out["type"] = "passage" if out.get("passage") else "discrete"
    out["skill"] = skill_for(subtype, t["cars"])
    out["subtype"] = subtype
    out["difficulty"] = difficulty
    out["correct"] = correct

    for key in ("passage", "figure"):
        if not out.get(key):
            out.pop(key, None)

    shift = zlib.crc32(out["id"].encode("utf-8")) % 4
    out["options"] = out["options"][shift:] + out["options"][:shift]
    out["correct"] = (out["correct"] - shift) % 4
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    tasks = build_tasks()
    out_path = os.path.join(OUT_DIR, "generated_topup.jsonl")
    print(f"{len(tasks)} topics; {PER_TOPIC} per topic", flush=True)

    idx = 1
    with open(out_path, "w", encoding="utf-8") as f:
        for ti, t in enumerate(tasks, 1):
            print(f"[{ti}/{len(tasks)}] {t['section']} / {t['subject']} / {t['topic']} ...", flush=True)
            try:
                data = chat(
                    [{"role": "system", "content": SYSTEM_PROMPT},
                     {"role": "user", "content": build_user(t)}],
                    temperature=0.85,
                    max_tokens=8192,
                )
            except Exception as e:
                print(f"  ERROR: {e}", flush=True)
                continue
            qs = data.get("questions", []) if isinstance(data, dict) else []
            got = 0
            for q in qs[:PER_TOPIC]:
                norm = normalize(q, t, idx)
                if norm is None:
                    continue
                f.write(json.dumps(norm, ensure_ascii=False) + "\n")
                f.flush()
                idx += 1
                got += 1
            print(f"  -> {got}", flush=True)

    n = sum(1 for _ in open(out_path, encoding="utf-8"))
    print(f"DONE: {n} questions -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
