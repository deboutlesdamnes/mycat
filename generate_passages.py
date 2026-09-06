# -*- coding: utf-8 -*-
"""Generate authentic MCAT practice-test PASSAGE sets (the majority of the exam).

Each passage-plan entry yields one PassageSpec (a ~500-word passage + figures),
validated against the framework and written as question_schema.json records to
workspace/generated_passage.jsonl. Science passages have exactly 5 questions;
CARS passages have 5-6 questions.

Usage: python generate_passages.py [--limit N]
"""
import argparse
import json
import os

from deepseek_backend import chat
from retrieve import retrieve
from gen_passage_config import build_passage_plan
from mcat_extract.longform import PassageSpec, LONGFORM_PASSAGE_SYSTEM, build_passage_user

OUT = r"c:\Users\jason\Documents\mycat\workspace\generated_passage.jsonl"
CK = r"c:\Users\jason\Documents\mycat\workspace\passage_checkpoint.json"


def main(limit=None):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tasks = build_passage_plan()["passages"]
    if limit:
        tasks = tasks[:limit]

    done = set()
    if os.path.exists(CK):
        done = set(json.load(open(CK, encoding="utf-8")))

    mode = "a" if done else "w"
    out = open(OUT, mode, encoding="utf-8")
    written = 0

    for t in tasks:
        key = f"{t['section']}|{t['subject']}|{t['topic']}"
        if key in done:
            continue
        print(f"PASSAGE {t['section']} / {t['subject']} / {t['topic']} ({t['n']} Q) ...", flush=True)
        excerpts = [ex["text"] for ex in retrieve(t["topic"], k=3)]
        base_user = build_passage_user(t["subject"], t["topic"], excerpts, n_questions=t["n"])

        spec = None
        errors = []
        for attempt in range(3):
            user = base_user
            if attempt and errors:
                user += (
                    "\n\nYour previous JSON was rejected by the validator for these reasons:\n"
                    + "\n".join(f"- {e}" for e in errors)
                    + "\n\nReturn a corrected JSON object. Make sure the passage is "
                    "420-650 words and the questions array has exactly the requested count."
                )
            try:
                data = chat(
                    [{"role": "system", "content": LONGFORM_PASSAGE_SYSTEM},
                     {"role": "user", "content": user}],
                    temperature=0.8,
                    max_tokens=8000,
                )
            except Exception as e:
                print(f"  ERROR: {e}", flush=True)
                break

            if not isinstance(data, dict):
                print("  ERROR: non-dict response", flush=True)
                break

            spec = PassageSpec.from_dict(data)
            # The plan is authoritative for metadata: the model's section/subject may be
            # lowercased or paraphrased, which would fail validation.
            spec.section = t["section"]
            spec.subject = t["subject"]
            spec.topic = t["topic"]
            spec.is_cars = bool(t.get("is_cars", False))
            if not spec.knowledge_points:
                spec.knowledge_points = [t["topic"]]
            if not spec.id:
                spec.id = f"passage-{len(done):03d}"

            errors = spec.validate()
            if not errors:
                break
            print(f"  attempt {attempt + 1} invalid ({len(errors)} errors); first: {errors[0]}", flush=True)

        if spec is None or errors:
            print(f"  SKIPPED after retries ({len(errors)} errors)", flush=True)
            continue

        for rec in spec.compile_to_schema():
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
        out.flush()
        written += 1
        done.add(key)
        with open(CK, "w", encoding="utf-8") as f:
            json.dump(sorted(done), f, ensure_ascii=False)

    out.close()
    print(f"DONE: {written} passage sets written to {OUT}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    main(limit=args.limit)
