# -*- coding: utf-8 -*-
"""Export the hard/complex scenario questions into a site-loadable JS deck."""
import json
import sys

INFILE = sys.argv[1] if len(sys.argv) > 1 else r"c:\Users\jason\Documents\mycat\workspace\generated_hard_demo.jsonl"
JS_OUT = sys.argv[2] if len(sys.argv) > 2 else r"c:\Users\jason\Documents\mycat\site\questions_hard.js"


def to_site(q):
    out = {
        "question": q["question"],
        "options": q["options"],
        "correct": q["correct"],
        "explanation": q["explanation"],
        "difficulty": q.get("difficulty", "hard"),
        "section": q.get("section", ""),
        "topic": q.get("topic", ""),
        "subject": q.get("subject", ""),
    }
    if q.get("passage"):
        out["passage"] = q["passage"]
    if q.get("figure"):
        out["figure"] = q["figure"]
        out["figure_caption"] = q.get("figure_caption", "")
    return out


def main():
    qs = [json.loads(l) for l in open(INFILE, encoding="utf-8") if l.strip()]
    deck = {
        "id": "hard-scenarios",
        "title": "Hard Scenarios",
        "section": "Hard / Complex Scenarios",
        "questions": [to_site(q) for q in qs],
    }
    js = (
        "// Hard / complex scenario questions (corpus-grounded).\n"
        "// Original content; not copied from AAMC or any copyrighted source.\n"
        "const HARD_DECKS = " + json.dumps([deck], ensure_ascii=False, indent=2) + ";\n"
    )
    with open(JS_OUT, "w", encoding="utf-8") as f:
        f.write(js)
    print(f"exported {len(qs)} hard questions -> {JS_OUT}")


if __name__ == "__main__":
    main()
