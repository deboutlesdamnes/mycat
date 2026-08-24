# -*- coding: utf-8 -*-
"""Generate structured MCAT questions from the knowledge base + templates."""
import json
import os
import zlib
from collections import Counter

from question_kb import FACTS, PREBUILT, SECTION_MAP
from question_templates import TEMPLATE_FUNCS

OUT_DIR = r"c:\Users\jason\Documents\mycat\workspace"


def _rotate(q):
    """Deterministically move the correct answer off position 0."""
    shift = zlib.crc32(q["id"].encode("utf-8")) % len(q["options"])
    q["options"] = q["options"][shift:] + q["options"][:shift]
    q["correct"] = (q["correct"] - shift) % len(q["options"])
    return q


def generate():
    questions = []
    seen = set()

    for fact in FACTS:
        for tname in fact.get("templates", []):
            q = TEMPLATE_FUNCS[tname](fact)
            if q["id"] in seen:
                raise SystemExit(f"duplicate id {q['id']}")
            seen.add(q["id"])
            questions.append(q)

    for p in PREBUILT:
        q = _rotate(dict(p))
        q.setdefault("section", SECTION_MAP.get(q["subject"], q["subject"]))
        if q["id"] in seen:
            raise SystemExit(f"duplicate id {q['id']}")
        seen.add(q["id"])
        questions.append(q)

    return questions



def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    questions = generate()

    with open(os.path.join(OUT_DIR, "generated.jsonl"), "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    with open(os.path.join(OUT_DIR, "generated.json"), "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"generated {len(questions)} questions")
    print(dict(Counter(q["subtype"] for q in questions)))


if __name__ == "__main__":
    main()
