# -*- coding: utf-8 -*-
"""Generate MCAT questions using the DeepSeek LLM backend.

Each task = (subject, topic, knowledge_point, question type, count). The model
returns questions in a minimal shape; metadata is filled in deterministically.
"""
import json
import os
import zlib
from collections import Counter

from deepseek_backend import chat
from question_kb import SECTION_MAP

OUT_DIR = r"c:\Users\jason\Documents\mycat\workspace"

SYSTEM_PROMPT = """\
You are an expert MCAT (Medical College Admission Test) question writer.
You write ORIGINAL, exam-style multiple-choice practice questions. Never copy
questions or wording from AAMC or any copyrighted prep material; write fresh,
scientifically accurate questions in your own words.

Return ONLY a single JSON object (no markdown fences, no commentary) with this
exact shape:
{"questions": [{"question": "...", "options": ["...","...","...","..."], "correct": 0, "explanation": "...", "passage": "..."}]}

Rules:
- "options" is always an array of EXACTLY 4 strings (displayed as A-D).
- "correct" is the integer index (0-3) of the single best answer.
- "explanation" is a concise paragraph that teaches why the correct answer is
  right and briefly why each wrong answer is wrong.
- Distractors must be plausible but unambiguously incorrect.
- "passage" is OPTIONAL: include it only for passage/data questions. When
  present, the question must require reading that passage/data.
- Keep questions appropriate for a pre-med MCAT science section.
"""

TYPE_HINTS = {
    "recall": "Write discrete (stand-alone) recall/application questions testing knowledge of a single concept (Skill 1).",
    "except": "Write 'All of the following ... EXCEPT' (or '... NOT') questions where one option is false and the other three are true.",
    "vignette": "Write a question whose stem contains a short clinical or experimental vignette, followed by a question about it.",
    "data-interp": "Write a question requiring data interpretation. Put the data description (graph/table/experiment) in the 'passage' field, then ask a question about it (Skill 4).",
    "passage": "Write a passage-based question: put a multi-sentence passage in the 'passage' field and ask a question that requires the passage plus background knowledge (Skill 2/3).",
}

TASKS = [
    {"subject": "Biology", "topic": "The Cell", "kp": "1.1 Cell Theory", "type": "recall", "n": 3},
    {"subject": "Biology", "topic": "The Cell", "kp": "1.2 Eukaryotic Cells", "type": "recall", "n": 3},
    {"subject": "Biology", "topic": "The Cell", "kp": "1.2 Eukaryotic Cells", "type": "except", "n": 2},
    {"subject": "Biology", "topic": "The Cell", "kp": "1.2 Eukaryotic Cells", "type": "vignette", "n": 2},
    {"subject": "Biology", "topic": "The Cell", "kp": "1.2 Eukaryotic Cells", "type": "data-interp", "n": 2},
    {"subject": "Biology", "topic": "Reproduction", "kp": "2.1 The Cell Cycle and Mitosis", "type": "recall", "n": 2},
    {"subject": "Biology", "topic": "Reproduction", "kp": "2.1 The Cell Cycle and Mitosis", "type": "passage", "n": 2},
]

SKILL_BY_TYPE = {
    "recall": "skill1",
    "except": "skill1",
    "vignette": "skill2",
    "data-interp": "skill4",
    "passage": "skill2",
}


def build_user_prompt(t):
    hint = TYPE_HINTS[t["type"]]
    return (
        f"Subject: {t['subject']}. Topic: {t['topic']} (knowledge point: {t['kp']}).\n"
        f"{hint}\n"
        f"Generate {t['n']} question(s). Return the JSON object now."
    )


def normalize(q, t, idx):
    """Fill metadata and enforce the structural invariants; return None if invalid."""
    if not isinstance(q, dict):
        return None
    opts = q.get("options")
    if not isinstance(opts, list) or len(opts) != 4 or not q.get("question"):
        return None
    correct = q.get("correct")
    try:
        correct = int(correct)
    except (TypeError, ValueError):
        return None
    if not (0 <= correct <= 3):
        return None

    q = dict(q)
    q["id"] = f"llm-{idx:03d}"
    q["section"] = SECTION_MAP.get(t["subject"], t["subject"])
    q["subject"] = t["subject"]
    q["topic"] = t["topic"]
    q["knowledge_point"] = t["kp"]
    q["type"] = "passage" if q.get("passage") else "discrete"
    q["skill"] = SKILL_BY_TYPE.get(t["type"], "skill1")
    q["subtype"] = t["type"]
    q["correct"] = correct
    # Strip empty optional fields (the model may return them as null).
    for key in ("passage", "figure"):
        if not q.get(key):
            q.pop(key, None)
    # Deterministically rotate options so the correct answer is not biased to one letter.
    shift = zlib.crc32(q["id"].encode("utf-8")) % 4
    q["options"] = q["options"][shift:] + q["options"][:shift]
    q["correct"] = (q["correct"] - shift) % 4
    return q


def generate():
    questions = []
    idx = 1
    total = len(TASKS)
    for ti, t in enumerate(TASKS, 1):
        user = build_user_prompt(t)
        print(f"[{ti}/{total}] {t['kp']} / {t['type']} ...", flush=True)
        try:
            data = chat(
                [{"role": "system", "content": SYSTEM_PROMPT},
                 {"role": "user", "content": user}],
                temperature=0.85,
                max_tokens=4096,
            )
        except Exception as e:
            print(f"  ERROR [{t['kp']} / {t['type']}]: {e}", flush=True)
            continue

        qs = data.get("questions", []) if isinstance(data, dict) else []
        got = 0
        for q in qs[:t["n"]]:
            norm = normalize(q, t, idx)
            if norm is None:
                continue
            questions.append(norm)
            idx += 1
            got += 1
        print(f"  -> {got} question(s)", flush=True)

    return questions


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    qs = generate()

    with open(os.path.join(OUT_DIR, "generated_llm.jsonl"), "w", encoding="utf-8") as f:
        for q in qs:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    with open(os.path.join(OUT_DIR, "generated_llm.json"), "w", encoding="utf-8") as f:
        json.dump(qs, f, ensure_ascii=False, indent=2)

    print(f"generated {len(qs)} questions via DeepSeek", flush=True)
    print(dict(Counter(q["subtype"] for q in qs)), flush=True)
    print("DONE", flush=True)



if __name__ == "__main__":
    main()
