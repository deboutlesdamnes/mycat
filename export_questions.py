# -*- coding: utf-8 -*-
"""Export generated questions to the site's deck format and to the SQLite DB."""
import json
import sqlite3
import sys
from collections import defaultdict

INFILE = sys.argv[1] if len(sys.argv) > 1 else r"c:\Users\jason\Documents\mycat\workspace\generated.jsonl"
DB = r"c:\Users\jason\Documents\mycat\mycat_knowledge.db"
JS_OUT = sys.argv[2] if len(sys.argv) > 2 else r"c:\Users\jason\Documents\mycat\site\questions_generated.js"
TABLE = sys.argv[3] if len(sys.argv) > 3 else "generated_questions"


def load():
    qs = []
    with open(INFILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                qs.append(json.loads(line))
    return qs


def to_site_question(q):
    out = {
        "question": q["question"],
        "options": q["options"],
        "correct": q["correct"],
        "explanation": q["explanation"],
    }
    if q.get("passage"):
        out["passage"] = q["passage"]
    return out


def main():
    qs = load()

    decks = defaultdict(list)
    for q in qs:
        decks[q["subject"]].append(q)

    deck_list = []
    for i, subject in enumerate(sorted(decks), start=1):
        qs_sub = decks[subject]
        deck_list.append({
            "id": f"gen{i}",
            "title": f"Generated {i}",
            "section": qs_sub[0]["section"],
            "questions": [to_site_question(q) for q in qs_sub],
        })

    js = (
        "// Auto-generated MCAT-style practice questions.\n"
        "// Original content; not copied from AAMC or any copyrighted source.\n"
        "const GENERATED_DECKS = " + json.dumps(deck_list, ensure_ascii=False, indent=2) + ";\n"
    )
    with open(JS_OUT, "w", encoding="utf-8") as f:
        f.write(js)

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE} (
        id TEXT PRIMARY KEY,
        section TEXT, subject TEXT, topic TEXT, knowledge_point TEXT,
        type TEXT, skill TEXT, subtype TEXT,
        passage TEXT, figure TEXT, question TEXT,
        options TEXT, correct INTEGER, explanation TEXT
    )""")
    c.execute(f"DELETE FROM {TABLE}")
    for q in qs:
        c.execute(
            f"""INSERT OR REPLACE INTO {TABLE}
               (id, section, subject, topic, knowledge_point, type, skill, subtype,
                passage, figure, question, options, correct, explanation)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (q["id"], q["section"], q["subject"], q["topic"], q["knowledge_point"],
             q["type"], q["skill"], q["subtype"], q.get("passage"), q.get("figure"),
             q["question"], json.dumps(q["options"], ensure_ascii=False),
             q["correct"], q["explanation"]),
        )
    conn.commit()
    n = c.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
    conn.close()

    print(f"exported {len(qs)} questions -> {JS_OUT}")
    print(f"stored {n} rows -> {DB} (table {TABLE})")


if __name__ == "__main__":
    main()
