# -*- coding: utf-8 -*-
"""Deterministic QA gate for generated questions (schema + structural checks)."""
import json
import os
import sys

from jsonschema import validate, ValidationError

SCHEMA = r"c:\Users\jason\Documents\mycat\question_schema.json"
INFILE = sys.argv[1] if len(sys.argv) > 1 else r"c:\Users\jason\Documents\mycat\workspace\generated.jsonl"
OUT = sys.argv[2] if len(sys.argv) > 2 else r"c:\Users\jason\Documents\mycat\workspace\validation_report.json"


def main():
    with open(SCHEMA, encoding="utf-8") as f:
        schema = json.load(f)

    questions = []
    with open(INFILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))

    errors = []
    seen_ids = set()
    seen_stems = {}

    for q in questions:
        qid = q.get("id", "<no id>")
        try:
            validate(q, schema)
        except ValidationError as e:
            errors.append({"id": qid, "issue": "schema", "detail": e.message})
            continue

        if q["id"] in seen_ids:
            errors.append({"id": qid, "issue": "duplicate_id"})
        seen_ids.add(q["id"])

        if len(q["options"]) != 4:
            errors.append({"id": qid, "issue": "option_count", "detail": len(q["options"])})

        if not (isinstance(q["correct"], int) and 0 <= q["correct"] <= 3):
            errors.append({"id": qid, "issue": "correct_range", "detail": q["correct"]})

        stem = q["question"].strip().lower()
        if stem in seen_stems:
            errors.append({"id": qid, "issue": "duplicate_stem", "dup_of": seen_stems[stem]})
        else:
            seen_stems[stem] = qid

    report = {
        "total": len(questions),
        "passed": len(questions) - len({e["id"] for e in errors}),
        "errors": errors,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"validated {report['total']} questions; {len(errors)} error(s)")
    for e in errors[:20]:
        print("  ", e)


if __name__ == "__main__":
    main()
