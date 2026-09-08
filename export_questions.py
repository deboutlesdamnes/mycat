# -*- coding: utf-8 -*-
"""Export generated questions to the site deck format and the SQLite DB."""
import json
import sqlite3
import sys
from collections import defaultdict

INFILE = sys.argv[1] if len(sys.argv) > 1 else r"c:\Users\jason\Documents\mycat\workspace\generated_full.jsonl"
DB = r"c:\Users\jason\Documents\mycat\mycat_knowledge.db"
JS_OUT = sys.argv[2] if len(sys.argv) > 2 else r"c:\Users\jason\Documents\mycat\site\questions_full.js"
TABLE = sys.argv[3] if len(sys.argv) > 3 else "generated_questions"

SECTION_META = {
    "Biological & Biochemical Foundations": ("full-bio", "Bio/Biochem Full-Length"),
    "Chemical & Physical Foundations": ("full-chem", "Chem/Phys Full-Length"),
    "Psychological, Social, & Biological Foundations": ("full-psysoc", "Psych/Soc Full-Length"),
    "Critical Analysis and Reasoning Skills": ("full-cars", "CARS Full-Length"),
}


def load():
    qs = []
    with open(INFILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                qs.append(json.loads(line))
    return qs


def share_passage_figures(qs):
    """A figure belongs to the passage, not to the one question that happened to
    cite it: every question sharing a passage must show the same reference image,
    or the prose ends up pointing at a figure that isn't on the page.

    Older passage runs attached the figure only to the questions whose
    figure_refs named it, so this fills in the rest of each set in place.
    """
    by_passage = defaultdict(list)
    for q in qs:
        if q.get("passage"):
            by_passage[q["passage"]].append(q)

    filled = 0
    for group in by_passage.values():
        source = next((q for q in group if q.get("figure")), None)
        if source is None:
            continue
        for q in group:
            if not q.get("figure"):
                q["figure"] = source["figure"]
                q["figure_type"] = source.get("figure_type", "")
                q["figure_caption"] = source.get("figure_caption", "")
                q["figure_alt"] = source.get("figure_alt", "")
                filled += 1
    return filled


def to_site_question(q):
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
    if q.get("figure"):
        out["figure"] = q["figure"]
        out["figure_caption"] = q.get("figure_caption", "")
        out["figure_type"] = q.get("figure_type", "")
    return out


def main():
    qs = load()
    filled = share_passage_figures(qs)
    if filled:
        print(f"attached the passage figure to {filled} sibling question(s)")

    decks = defaultdict(list)
    for q in qs:
        decks[q["section"]].append(q)

    deck_list = []
    for section, qs_section in decks.items():
        did, title = SECTION_META.get(section, ("full", section))
        deck_list.append({
            "id": did,
            "title": title,
            "section": section,
            "questions": [to_site_question(q) for q in qs_section],
        })

    order = {did: i for i, (did, _) in enumerate(SECTION_META.values())}
    deck_list.sort(key=lambda d: order.get(d["id"], 99))

    js = (
        "// Auto-generated full-length MCAT practice questions (DeepSeek).\n"
        "// Original content; not copied from AAMC or any copyrighted source.\n"
        "const FULL_DECKS = " + json.dumps(deck_list, ensure_ascii=False, indent=2) + ";\n"
    )
    with open(JS_OUT, "w", encoding="utf-8") as f:
        f.write(js)

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(f"DROP TABLE IF EXISTS {TABLE}")
    c.execute(f"""CREATE TABLE {TABLE} (
        id TEXT PRIMARY KEY,
        section TEXT, subject TEXT, topic TEXT, knowledge_point TEXT,
        type TEXT, skill TEXT, subtype TEXT, difficulty TEXT,
        passage TEXT, figure TEXT, figure_caption TEXT, figure_type TEXT, question TEXT,
        options TEXT, correct INTEGER, explanation TEXT
    )""")
    for q in qs:
        cols = ["id", "section", "subject", "topic", "knowledge_point", "type",
                "skill", "subtype", "difficulty", "passage", "figure",
                "figure_caption", "figure_type", "question", "options",
                "correct", "explanation"]
        vals = [q["id"], q["section"], q["subject"], q["topic"], q["knowledge_point"],
                q["type"], q["skill"], q["subtype"], q.get("difficulty"),
                q.get("passage"), q.get("figure"), q.get("figure_caption"),
                q.get("figure_type"), q["question"],
                json.dumps(q["options"], ensure_ascii=False),
                q["correct"], q["explanation"]]
        ph = ",".join(["?"] * len(cols))
        c.execute(
            f"INSERT OR REPLACE INTO {TABLE} ({','.join(cols)}) VALUES ({ph})",
            vals,
        )
    conn.commit()
    n = c.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
    conn.close()

    print(f"exported {len(qs)} questions -> {JS_OUT}")
    print(f"stored {n} rows -> {DB} (table {TABLE})")


if __name__ == "__main__":
    main()
