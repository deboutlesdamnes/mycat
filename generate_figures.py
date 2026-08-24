# -*- coding: utf-8 -*-
"""Pair questions with MCAT-style figures.

For selected questions (data-interpretation + Organic Chemistry), ask DeepSeek
to produce a structured "figure spec", render it to inline SVG with figure_lib,
and attach figure / figure_caption / figure_type / figure_alt to the question.
"""
import json
import os

from deepseek_backend import chat
from figure_lib import render_figure

INFILE = r"c:\Users\jason\Documents\mycat\workspace\generated_full.jsonl"
OUTFILE = r"c:\Users\jason\Documents\mycat\workspace\generated_full_fig.jsonl"
CHECKPOINT = r"c:\Users\jason\Documents\mycat\workspace\figures_checkpoint.json"

FIGURE_SYSTEM = """\
You convert an MCAT question into a structured FIGURE specification (JSON) that
a renderer will draw as SVG. Return ONLY a JSON object:
{"figure": {...}, "caption": "Figure N. ..."}

Choose ONE "type" and fill its required fields:

- "line":    {"type":"line","title":str,"xLabel":str,"yLabel":str,"series":[{"name":str,"points":[[x,y],...]}]}
- "bar":     {"type":"bar","title":str,"xLabel":str,"yLabel":str,"series":[{"name":str,"points":[[x,y],...]}]}
- "scatter": {"type":"scatter","title":str,"xLabel":str,"yLabel":str,"series":[{"name":str,"points":[[x,y],...]}]}
- "table":   {"type":"table","columns":[str,...],"rows":[[...],...]}
- "spectrum":{"type":"spectrum","kind":"1h-nmr"|"13c-nmr"|"ir","title":str,
              "peaks":[{"ppm":num,"multiplicity":"s|d|t|q|m","integration":int}]}
              (for IR, use peaks as {"wavenumber":num,"intensity":num,"label":str} and add "wavenumberRange":[400,4000])
- "diagram": {"type":"diagram","title":str,"nodes":[{"id":str,"label":str,"x":int,"y":int,"w":int,"h":int}],
              "edges":[{"from":str,"to":str,"label":str}]}
- "molecule": {"type":"molecule","smiles":str}

Rules:
- The figure MUST be directly relevant to the question and its CORRECT answer.
- Use realistic, internally consistent values (a correct curve, a chemically valid SMILES).
- ALL numeric values (points, ppm, wavenumber, integration, intensity) must be plain numbers with no "%", units, or labels (e.g. 50 not "50%").
- If the question/passage already contains data (table, numbers, a spectrum, a pathway, a molecule), turn THAT data into the figure.
- Keep it simple and MCAT-like.
"""


def should_figure(q):
    if q.get("subtype") == "data-interp":
        return True
    if q.get("subject") == "Organic Chemistry":
        return True
    return False


def build_user(q):
    return (
        f"Question: {q['question']}\n"
        f"Passage/data: {q.get('passage', '')}\n"
        f"Options: {q['options']}\n"
        f"Correct answer index: {q['correct']}\n"
        f"Explanation: {q['explanation']}\n"
        f"Subject / topic: {q['subject']} / {q['topic']}\n"
        f"Produce the figure spec JSON now."
    )


def validate_and_render(spec, qid):
    fig = spec.get("figure") if isinstance(spec, dict) else None
    if not isinstance(fig, dict):
        return None
    t = fig.get("type")
    if t not in ("line", "bar", "scatter", "table", "spectrum", "diagram", "molecule"):
        return None
    try:
        svg = render_figure(fig)
    except Exception as e:
        print(f"  render error {qid}: {e}", flush=True)
        return None
    if not svg or "(no data)" in svg or "(invalid" in svg or "(empty" in svg:
        return None
    if t == "molecule":
        try:
            from rdkit import Chem
            if Chem.MolFromSmiles(fig.get("smiles", "")) is None:
                return None
        except Exception:
            return None
    return {
        "figure": svg,
        "figure_type": t,
        "figure_caption": spec.get("caption", ""),
        "figure_alt": fig.get("title", ""),
    }


def main():
    questions = [json.loads(l) for l in open(INFILE, encoding="utf-8") if l.strip()]
    selected = [q for q in questions if should_figure(q)]
    print(f"{len(questions)} questions; {len(selected)} selected for figures", flush=True)

    updates = {}
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT, encoding="utf-8") as f:
            updates = json.load(f)
        print(f"resuming with {len(updates)} already done", flush=True)

    for i, q in enumerate(selected, 1):
        if q["id"] in updates:
            continue
        print(f"[{i}/{len(selected)}] {q['id']} ({q['subtype']}, {q['topic']}) ...", flush=True)
        try:
            spec = chat(
                [{"role": "system", "content": FIGURE_SYSTEM},
                 {"role": "user", "content": build_user(q)}],
                temperature=0.4,
                max_tokens=2048,
            )
        except Exception as e:
            print(f"  ERROR {q['id']}: {e}", flush=True)
            continue
        fig = validate_and_render(spec, q["id"])
        if fig is None:
            print(f"  -> no valid figure", flush=True)
            continue
        updates[q["id"]] = fig
        with open(CHECKPOINT, "w", encoding="utf-8") as f:
            json.dump(updates, f, ensure_ascii=False, indent=2)
        print(f"  -> {fig['figure_type']}", flush=True)

    # merge and write full output
    for q in questions:
        if q["id"] in updates:
            q.update(updates[q["id"]])
    with open(OUTFILE, "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    n = sum(1 for q in questions if q.get("figure"))
    print(f"DONE: {n} questions now have figures -> {OUTFILE}", flush=True)


if __name__ == "__main__":
    main()
