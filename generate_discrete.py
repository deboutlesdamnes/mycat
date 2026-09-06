# -*- coding: utf-8 -*-
"""Generate the DISCRETE (stand-alone) minority of the full-length exam.

Uses the same LLM writer as generate_questions_llm but never emits a passage, so
every record is type=discrete. Writes workspace/generated_discrete.jsonl.
"""
import argparse
import json
import os

from deepseek_backend import chat
from gen_passage_config import build_passage_plan
from generate_questions_llm import SYSTEM_PROMPT, normalize

OUT = r"c:\Users\jason\Documents\mycat\workspace\generated_discrete.jsonl"
CK = r"c:\Users\jason\Documents\mycat\workspace\discrete_checkpoint.json"


def build_user(t):
    return (
        f"Subject: {t['subject']}. Topic: {t['topic']}. Write {t['n']} DISCRETE "
        f"(stand-alone) questions — do NOT include any passage. Vary the subtypes among: "
        f"recall, except, compare, sequence, vignette, predict, yes-no. Assign each a "
        f"difficulty (easy/medium/hard), roughly balanced. Return the JSON."
    )


def main(limit=None):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tasks = build_passage_plan()["discrete"]
    if limit:
        tasks = tasks[:limit]

    done = set()
    if os.path.exists(CK):
        done = set(json.load(open(CK, encoding="utf-8")))

    mode = "a" if done else "w"
    out = open(OUT, mode, encoding="utf-8")
    idx = sum(1 for _ in open(OUT, encoding="utf-8")) + 1 if mode == "a" else 1

    for t in tasks:
        key = f"{t['section']}|{t['subject']}|{t['topic']}"
        if key in done:
            continue
        print(f"DISCRETE {t['section']} / {t['subject']} / {t['topic']} ({t['n']}) ...", flush=True)
        try:
            data = chat(
                [{"role": "system", "content": SYSTEM_PROMPT},
                 {"role": "user", "content": build_user(t)}],
                temperature=0.85,
                max_tokens=4096,
            )
        except Exception as e:
            print(f"  ERROR: {e}", flush=True)
            continue

        qs = data.get("questions", []) if isinstance(data, dict) else []
        got = 0
        for q in qs[:t["n"]]:
            norm = normalize(q, t, idx)
            if norm is None:
                continue
            out.write(json.dumps(norm, ensure_ascii=False) + "\n")
            out.flush()
            idx += 1
            got += 1
        done.add(key)
        with open(CK, "w", encoding="utf-8") as f:
            json.dump(sorted(done), f, ensure_ascii=False)
        print(f"  -> {got} question(s)", flush=True)

    out.close()
    print(f"DONE -> {OUT}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    main(limit=args.limit)
