# -*- coding: utf-8 -*-
"""Print an overview of extracted/images_extracted.json for verification."""
import json

data = json.load(open(r"extracted/images_extracted.json", encoding="utf-8"))
by_section = {}
for rec in data:
    by_section.setdefault(rec["section"], []).append(rec)

for si in sorted(by_section):
    recs = by_section[si]
    passages = {}
    standalone = []
    for r in recs:
        if r["kind"] == "passage":
            p = r["passage"]
            passages.setdefault(p, {
                "range": r["passage_question_range"],
                "questions": [],
                "figures": list(r["figures"].keys()),
                "tables": {k: len(v["rows"]) for k, v in r["tables"].items()},
                "passage_len": len(r["passage_text"]),
            })
            passages[p]["questions"].append(r["question"])
        else:
            standalone.append(r["question"])
    print(f"=== Section {si} ({recs[0]['subject']}) ===")
    for p in sorted(passages):
        info = passages[p]
        figs = ", ".join(f"{k}:{data[0]['figures'].get(k,{}).get('caption','') if False else ''}" for k in info["figures"])
        print(f"  Passage {p} Q{info['range'][0]}-{info['range'][1]}: questions={info['questions']} | figures={info['figures']} | tables={info['tables']} | text_chars={info['passage_len']}")
    print(f"  Standalone questions: {standalone}")
    print()
