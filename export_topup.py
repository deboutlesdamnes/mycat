# -*- coding: utf-8 -*-
"""Export the top-up questions to the site, deduped against the existing bank."""
import json
import os
import re

ROOT = r"c:\Users\jason\Documents\mycat"
WS = os.path.join(ROOT, "workspace")


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def existing_stems():
    stems = set()
    for fn in ["generated_full_fig.jsonl", "generated_hard_demo.jsonl", "generated_scenario.jsonl"]:
        for q in load_jsonl(os.path.join(WS, fn)):
            if q.get("question"):
                stems.add(norm(q["question"]))
    # hand-written questions.js (JS object syntax -> count + rough stems via regex)
    text = open(os.path.join(ROOT, "site", "questions.js"), encoding="utf-8").read()
    for m in re.finditer(r"question:\s*[\"'](.*?)[\"']", text, re.DOTALL):
        stems.add(norm(m.group(1)))
    return stems


def to_site(q):
    out = {
        "question": q["question"],
        "options": q["options"],
        "correct": q["correct"],
        "explanation": q["explanation"],
        "difficulty": q.get("difficulty", "medium"),
        "section": q.get("section", ""),
        "topic": q.get("topic", ""),
        "subject": q.get("subject", ""),
    }
    if q.get("passage"):
        out["passage"] = q["passage"]
    return out


def main():
    topup = load_jsonl(os.path.join(WS, "generated_topup.jsonl"))
    seen = existing_stems()
    deduped = []
    for q in topup:
        if not q.get("question"):
            continue
        s = norm(q["question"])
        if s in seen:
            continue
        seen.add(s)
        deduped.append(q)

    deck = {
        "id": "topup-set",
        "title": "Additional Practice",
        "section": "Mixed additional practice",
        "questions": [to_site(q) for q in deduped],
    }
    js = "const TOPUP_DECKS = " + json.dumps([deck], ensure_ascii=False, indent=2) + ";\n"
    out = os.path.join(ROOT, "site", "questions_topup.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write(js)

    # report
    total = len(seen)  # unique after dedup (existing + new)
    print(f"topup: {len(topup)} -> deduped {len(deduped)} added to {total} unique MCQ stems")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
