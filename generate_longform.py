# -*- coding: utf-8 -*-
"""Generate two long-form question types, grounded in corpus excerpts:

1. ESSAY questions — open-ended "concept check" style (like the MCAT Concept
   Checks in the review books) with a model answer and rubric key points.
2. SCENARIO-based long questions — a research scenario passage followed by
   3-4 multiple-choice questions requiring scenario + background reasoning.

Both use retrieve.py to pull corpus excerpts for grounding.
"""
import json
import os
from collections import Counter

from deepseek_backend import chat
from retrieve import retrieve
from gen_config import build_tasks

OUT_DIR = r"c:\Users\jason\Documents\mycat\workspace"

SECTION_MAP = {
    "Biology": "Biological & Biochemical Foundations",
    "Biochemistry": "Biological & Biochemical Foundations",
    "General Chemistry": "Chemical & Physical Foundations",
    "Organic Chemistry": "Chemical & Physical Foundations",
    "Physics": "Chemical & Physical Foundations",
    "Psychology": "Psychological, Social, & Biological Foundations",
    "Sociology": "Psychological, Social, & Biological Foundations",
    "Critical Analysis and Reasoning Skills (CARS)": "Critical Analysis and Reasoning Skills",
}

LONGFORM_SYSTEM = """\
You are an expert MCAT question writer. You create TWO types of study material,
both GROUNDED in the reference excerpts from a study corpus provided below:

1. ESSAY question — an open-ended "concept check" style question (like the MCAT
   Concept Checks in review books) that requires a written explanation. Provide:
   - "prompt": the open-ended question (no answer options).
   - "model_answer": a 2-5 sentence model answer.
   - "key_points": 3-5 rubric bullets the answer must hit.

2. SCENARIO-based long question — a research/experimental scenario passage (like
   the research passages in review books) followed by 3-4 multiple-choice
   questions that require reasoning with the scenario plus background knowledge.

Ground everything in the corpus excerpts: use their terminology, examples, and depth.

Return ONLY a JSON object:
{"essay": {"prompt":"...", "model_answer":"...", "key_points":["...","..."], "difficulty":"medium"},
 "scenario": {"scenario":"...", "questions":[{"question":"...","options":["A","B","C","D"],"correct":0,"explanation":"..."}]}}

Rules:
- essay.prompt is open-ended. model_answer is 2-5 sentences. key_points is 3-5 bullets.
- scenario.scenario is a multi-sentence research/experimental passage.
- scenario.questions is 3-4 MCQs; each has exactly 4 options, correct (0-based index),
  and a teaching explanation.
- difficulty is "easy", "medium", or "hard".
- Original content only; do not copy from the excerpts verbatim.
"""


def build_user(t):
    excerpts = retrieve(t["topic"], k=3)
    ref = ""
    for i, ex in enumerate(excerpts, 1):
        ref += f"\n--- excerpt {i} (file: {ex['file']}, score {ex['score']}) ---\n{ex['text']}\n"
    if not ref:
        ref = "(no corpus excerpt found)"
    return (
        f"Subject: {t['subject']}. Topic: {t['topic']}.\n"
        f"Reference material from the study corpus (ground your questions in this):\n{ref}\n"
        f"Generate 1 essay question and 1 scenario-based long question. Return JSON."
    )


def _count(path):
    if not os.path.exists(path):
        return 0
    return sum(1 for _ in open(path, encoding="utf-8"))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    tasks = build_tasks()
    essay_path = os.path.join(OUT_DIR, "generated_essay.jsonl")
    scen_path = os.path.join(OUT_DIR, "generated_scenario.jsonl")
    ck_path = os.path.join(OUT_DIR, "longform_checkpoint.json")

    done = set()
    if os.path.exists(ck_path):
        done = set(json.load(open(ck_path, encoding="utf-8")))
    print(f"{len(tasks)} topics; {len(done)} done; {len(tasks) - len(done)} to do", flush=True)

    mode = "a" if done else "w"
    ei = _count(essay_path) + 1
    si = _count(scen_path) + 1
    ef = open(essay_path, mode, encoding="utf-8")
    sf = open(scen_path, mode, encoding="utf-8")

    for t in tasks:
        key = f"{t['subject']}|{t['topic']}"
        if key in done:
            continue
        print(f"TOPIC {t['subject']} / {t['topic']} ...", flush=True)
        try:
            data = chat(
                [{"role": "system", "content": LONGFORM_SYSTEM},
                 {"role": "user", "content": build_user(t)}],
                temperature=0.8,
                max_tokens=8000,
            )
        except Exception as e:
            print(f"  ERROR: {e}", flush=True)
            continue

        e = data.get("essay") if isinstance(data, dict) else None
        if isinstance(e, dict) and e.get("prompt"):
            eq = {
                "id": f"essay-{ei:03d}",
                "type": "essay",
                "subject": t["subject"],
                "topic": t["topic"],
                "section": SECTION_MAP.get(t["subject"], t["subject"]),
                "difficulty": e.get("difficulty") if e.get("difficulty") in ("easy", "medium", "hard") else "medium",
                "prompt": e["prompt"],
                "model_answer": e.get("model_answer", ""),
                "key_points": e.get("key_points", []),
            }
            ef.write(json.dumps(eq, ensure_ascii=False) + "\n")
            ef.flush()
            ei += 1

        s = data.get("scenario") if isinstance(data, dict) else None
        if isinstance(s, dict) and s.get("scenario"):
            for q in s.get("questions", []):
                if not isinstance(q, dict) or not q.get("question") or not q.get("options"):
                    continue
                opts = q.get("options")
                if not isinstance(opts, list) or len(opts) != 4:
                    continue
                try:
                    correct = int(q.get("correct"))
                except (TypeError, ValueError):
                    continue
                if not (0 <= correct <= 3):
                    continue
                sq = {
                    "id": f"scenario-{si:03d}",
                    "type": "passage",
                    "subtype": "scenario",
                    "subject": t["subject"],
                    "topic": t["topic"],
                    "section": SECTION_MAP.get(t["subject"], t["subject"]),
                    "knowledge_point": t["topic"],
                    "skill": "skill2",
                    "difficulty": q.get("difficulty") if q.get("difficulty") in ("easy", "medium", "hard") else "hard",
                    "passage": s["scenario"],
                    "question": q["question"],
                    "options": opts,
                    "correct": correct,
                    "explanation": q.get("explanation", ""),
                }
                sf.write(json.dumps(sq, ensure_ascii=False) + "\n")
                sf.flush()
                si += 1

        done.add(key)
        with open(ck_path, "w", encoding="utf-8") as f:
            json.dump(sorted(done), f, ensure_ascii=False)
        print(f"  -> essay={ei - 1}, scenario={si - 1}", flush=True)

    ef.close()
    sf.close()
    print(f"DONE: {ei - 1} essay, {si - 1} scenario sub-questions", flush=True)


if __name__ == "__main__":
    main()

