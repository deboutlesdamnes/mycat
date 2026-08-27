# -*- coding: utf-8 -*-
"""Export long-form questions to site data files:
- essay questions -> site/questions_essay.js  (ESSAY_QUESTIONS)
- scenario MCQs   -> site/questions_scenario.js (SCENARIO_DECKS)
"""
import json
import sys

ESSAY_IN = r"c:\Users\jason\Documents\mycat\workspace\generated_essay.jsonl"
SCEN_IN = r"c:\Users\jason\Documents\mycat\workspace\generated_scenario.jsonl"
ESSAY_OUT = r"c:\Users\jason\Documents\mycat\site\questions_essay.js"
SCEN_OUT = r"c:\Users\jason\Documents\mycat\site\questions_scenario.js"


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
    return out


def main():
    essays = [json.loads(l) for l in open(ESSAY_IN, encoding="utf-8") if l.strip()]
    js = "// Essay / concept-check questions (open-ended, with model answers).\n" \
         "const ESSAY_QUESTIONS = " + json.dumps(essays, ensure_ascii=False, indent=2) + ";\n"
    with open(ESSAY_OUT, "w", encoding="utf-8") as f:
        f.write(js)

    scens = [json.loads(l) for l in open(SCEN_IN, encoding="utf-8") if l.strip()]
    deck = {
        "id": "scenario-set",
        "title": "Scenario Questions",
        "section": "Scenario-based practice",
        "questions": [to_site(q) for q in scens],
    }
    js = "// Scenario-based long questions (research passages).\n" \
         "const SCENARIO_DECKS = " + json.dumps([deck], ensure_ascii=False, indent=2) + ";\n"
    with open(SCEN_OUT, "w", encoding="utf-8") as f:
        f.write(js)

    print(f"exported {len(essays)} essay + {len(scens)} scenario questions")


if __name__ == "__main__":
    main()
