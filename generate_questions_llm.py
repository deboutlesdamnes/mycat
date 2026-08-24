# -*- coding: utf-8 -*-
"""Generate full-length MCAT questions using the DeepSeek LLM backend.

Reads the generation spec from gen_config.py, batches one API call per topic,
and writes questions incrementally to workspace/generated_full.jsonl.
"""
import json
import os
import zlib
from collections import Counter

from deepseek_backend import chat
from gen_config import build_tasks

OUT_DIR = r"c:\Users\jason\Documents\mycat\workspace"

SYSTEM_PROMPT = """\
You are an expert MCAT (Medical College Admission Test) question writer.
Write ORIGINAL, exam-style multiple-choice practice questions in your own words.
Never copy questions or wording from AAMC or any copyrighted prep material.

Return ONLY a single JSON object (no markdown fences, no commentary) with this
exact shape:
{"questions": [{"question": "...", "options": ["A","B","C","D"], "correct": 0, "explanation": "...", "passage": "...", "difficulty": "medium", "subtype": "recall"}]}

Rules:
- "options" is always an array of EXACTLY 4 strings (shown as A-D).
- "correct" is the integer index (0-3) of the single best answer.
- "explanation" is a concise paragraph teaching why the correct answer is right
  and briefly why each wrong answer is wrong.
- "difficulty" is one of "easy", "medium", or "hard". Aim for a balanced mix.
- "subtype" is a short label describing the question type (see the user message).
- "passage" is OPTIONAL: include it only for passage/data/CARS questions; when
  present, the question must require reading that passage/data.
- Distractors must be plausible but unambiguously incorrect.
- Keep questions appropriate for a pre-med MCAT section.
"""

SCIENCE_SKILLS = {
    "recall": "skill1", "except": "skill1", "compare": "skill1",
    "sequence": "skill1", "yes-no": "skill1",
    "vignette": "skill2", "predict": "skill2", "passage": "skill2",
    "data-interp": "skill4",
}
CARS_SKILLS = {
    "main-idea": "cars-foc", "detail": "cars-foc", "function": "cars-foc",
    "def-context": "cars-foc",
    "inference": "cars-rwt", "strengthen-weaken": "cars-rwt",
    "apply": "cars-rbt",
}


def skill_for(subtype, cars):
    if cars:
        return CARS_SKILLS.get(subtype, "cars-rwt")
    return SCIENCE_SKILLS.get(subtype, "skill1")


def build_user_prompt(t):
    if t["cars"]:
        return (
            f"Write {t['n']} CARS (Critical Analysis and Reasoning Skills) passage-based "
            f"questions on the theme: {t['topic']}. Provide ONE shared passage in the "
            f"'passage' field of every question. Cover a mix of CARS skills: Foundations of "
            f"Comprehension (subtypes: main-idea, detail, function, def-context), Reasoning "
            f"Within the Text (subtypes: inference, strengthen-weaken), and Reasoning Beyond "
            f"the Text (subtypes: apply, strengthen-weaken). Assign each a difficulty "
            f"(easy/medium/hard), roughly balanced. Return the JSON."
        )
    return (
        f"Subject: {t['subject']}. Topic: {t['topic']}. Write {t['n']} questions. "
        f"Vary the subtypes among: recall, except, vignette, data-interp, passage, compare, "
        f"sequence, predict, yes-no. For data-interp and passage questions, put the data or "
        f"passage in the 'passage' field. Assign each question a difficulty (easy/medium/hard), "
        f"roughly balanced. Return the JSON."
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
    out["id"] = f"llm-{idx:03d}"
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
    target = sum(t["n"] for t in tasks)
    print(f"{len(tasks)} tasks, {target} questions target", flush=True)

    out_path = os.path.join(OUT_DIR, "generated_full.jsonl")
    idx = 1
    with open(out_path, "w", encoding="utf-8") as f:
        for ti, t in enumerate(tasks, 1):
            user = build_user_prompt(t)
            print(f"[{ti}/{len(tasks)}] {t['section']} / {t['subject']} / {t['topic']} ({t['n']}) ...", flush=True)
            try:
                data = chat(
                    [{"role": "system", "content": SYSTEM_PROMPT},
                     {"role": "user", "content": user}],
                    temperature=0.85,
                    max_tokens=8192,
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
                f.write(json.dumps(norm, ensure_ascii=False) + "\n")
                f.flush()
                idx += 1
                got += 1
            print(f"  -> {got} question(s)", flush=True)

    qs = [json.loads(l) for l in open(out_path, encoding="utf-8") if l.strip()]
    with open(out_path.replace(".jsonl", ".json"), "w", encoding="utf-8") as f:
        json.dump(qs, f, ensure_ascii=False, indent=2)

    print(f"DONE: {len(qs)} questions -> {out_path}", flush=True)
    print(dict(Counter(q["difficulty"] for q in qs)), flush=True)
    print(dict(Counter(q["section"] for q in qs)), flush=True)


if __name__ == "__main__":
    main()

