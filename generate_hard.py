# -*- coding: utf-8 -*-
"""Generate complex, corpus-grounded MCAT scenario questions (hard/medium only).

For each topic we retrieve relevant corpus excerpts and pass them into the
prompt as reference material, so the generated questions use the corpus's
terminology, examples, and depth — and are required to be passage-based,
multi-step, experimental/data questions (Science Skills 2/3/4).
"""
import json
import os
from collections import Counter

from deepseek_backend import chat
from retrieve import retrieve

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

HARD_SYSTEM = """\
You are an expert MCAT question writer who creates DIFFICULT, complex, passage-based
questions. You are given a topic, reference excerpts from a study corpus, and a
difficulty target.

Requirements:
- Write PASSAGE-BASED or experimental/data scenarios — never single-concept recall.
- Require MULTI-STEP reasoning that integrates 2+ concepts (Science Skills 2, 3, 4:
  scientific reasoning, experimental design, and data/statistical reasoning).
- GROUND the question in the provided corpus excerpts: use their terminology,
  examples, and depth of detail.
- difficulty must be "hard" or "medium" only (never "easy").
- Use complex-scenario patterns such as: "Researchers did X ... which experiment would
  best test ...?", "Figure/Table shows ... which conclusion is best supported?",
  a multi-step calculation + reasoning, or cross-topic integration.

Return ONLY a JSON object:
{"questions": [{"question":"...","options":["A","B","C","D"],"correct":0,"explanation":"...","passage":"...","difficulty":"hard","subtype":"passage"}]}

Rules:
- options is always exactly 4 strings; correct is the 0-based index.
- explanation teaches why the correct answer is right and why each wrong answer is wrong.
- passage is REQUIRED (a research scenario, experiment, or data description).
"""

DEMO_TOPICS = [
    {"subject": "Biology", "topic": "Genetics and Evolution", "n": 2},
    {"subject": "General Chemistry", "topic": "Acids and Bases", "n": 2},
    {"subject": "General Chemistry", "topic": "Chemical Kinetics", "n": 2},
    {"subject": "Physics", "topic": "Kinematics and Dynamics", "n": 2},
]


def build_user(t):
    excerpts = retrieve(t["topic"], k=3)
    ref = ""
    for i, ex in enumerate(excerpts, 1):
        ref += f"\n--- excerpt {i} (file: {ex['file']}, score {ex['score']}) ---\n{ex['text']}\n"
    if not ref:
        ref = "(no corpus excerpt found)"
    return (
        f"Subject: {t['subject']}. Topic: {t['topic']}.\n"
        f"Difficulty target: hard/medium only.\n"
        f"Reference material from the study corpus (ground your question in this):\n{ref}\n"
        f"Generate {t['n']} complex scenario question(s). Return JSON."
    )


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "generated_hard_demo.jsonl")
    all_qs = []
    idx = 1

    for t in DEMO_TOPICS:
        print(f"TOPIC {t['topic']} ({t['subject']}) ...", flush=True)
        try:
            data = chat(
                [{"role": "system", "content": HARD_SYSTEM},
                 {"role": "user", "content": build_user(t)}],
                temperature=0.8,
                max_tokens=6000,
            )
        except Exception as e:
            print(f"  ERROR: {e}", flush=True)
            continue

        qs = data.get("questions", []) if isinstance(data, dict) else []
        got = 0
        for q in qs[:t["n"]]:
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

            q = dict(q)
            q["id"] = f"hard-{idx:02d}"
            idx += 1
            q["section"] = SECTION_MAP.get(t["subject"], t["subject"])
            q["subject"] = t["subject"]
            q["topic"] = t["topic"]
            q["knowledge_point"] = t["topic"]
            q["type"] = "passage" if q.get("passage") else "discrete"
            q["skill"] = q.get("skill", "skill2")
            q["subtype"] = q.get("subtype", "passage")
            q["difficulty"] = q.get("difficulty") if q.get("difficulty") in ("hard", "medium") else "hard"
            q["correct"] = correct
            all_qs.append(q)
            got += 1
        print(f"  -> {got} question(s)", flush=True)

    with open(out_path, "w", encoding="utf-8") as f:
        for q in all_qs:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    with open(out_path.replace(".jsonl", ".json"), "w", encoding="utf-8") as f:
        json.dump(all_qs, f, ensure_ascii=False, indent=2)

    print(f"DONE: {len(all_qs)} hard demo questions -> {out_path}", flush=True)
    print(dict(Counter(q["difficulty"] for q in all_qs)), flush=True)


if __name__ == "__main__":
    main()
