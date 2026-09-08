# -*- coding: utf-8 -*-
"""Add a reference figure to already-generated science passages that lack one.

The passage pipeline (generate_passages.py) now requires every science passage to
ship a figure, but the older scenario/top-up banks were written without any. This
backfills them *additively*: the existing passage text and questions are kept as
they are, and the model is asked only for

  1. a figure spec that figure_lib can draw from the data the passage describes, and
  2. one sentence citing it, appended to the passage as its closing line,

so nothing that the existing questions depend on is rewritten. Every question
sharing the passage gets the figure, matching how the player renders a set.

Usage: python backfill_figures.py workspace/generated_scenario.jsonl [--limit N]
"""
import argparse
import json
import os
import re

from deepseek_backend import chat
from mcat_extract.longform import FigureSpec

CK_SUFFIX = ".figure_backfill.json"

SYSTEM = """\
You add a data figure to an existing MCAT practice passage.

You are given a passage and the questions asked about it. Design the ONE figure a
test-taker would expect to see with this passage: the data the passage describes,
drawn so values can be read off it. Do not contradict the passage.

Return ONLY a JSON object:

{
  "figure": {
    "type": "line|bar|scatter|table|spectrum|diagram",
    "caption": "Figure 1. ...",
    "alt": "...",
    "spec": { ... }
  },
  "citation_sentence": "One sentence, containing the exact text \\"Figure 1\\", that
                        points the reader at the figure and says what it shows."
}

The spec must carry real numbers and use one of these shapes exactly:
  line/bar/scatter: {"type":"line","title":"...","xLabel":"...","yLabel":"...",
                     "series":[{"name":"...","points":[[x,y],[x,y],...]}]}
  table:            {"type":"table","columns":["...","..."],"rows":[["...","..."],...]}
  spectrum:         {"type":"spectrum","kind":"1h-nmr","title":"...",
                     "peaks":[{"shift":7.2,"height":0.8,"label":"..."}]}
  diagram:          {"type":"diagram","title":"...","nodes":[{"id":"a","label":"..."}],
                     "edges":[{"from":"a","to":"b","label":"..."}]}

For a bar chart use the condition names as the x values ([["Control",35],...]) so the
axis is labelled. Empty or placeholder specs are rejected.
"""


def build_user(passage, questions):
    stems = "\n".join(f"- {q}" for q in questions)
    return (
        f"Passage:\n{passage}\n\n"
        f"Questions asked about it:\n{stems}\n\n"
        "Design the figure this passage should be read with. Return JSON."
    )


def is_science(rec):
    return "Critical Analysis" not in (rec.get("section") or "")


def group_passages(recs):
    """Passage text -> its records, in file order."""
    groups = {}
    for r in recs:
        if r.get("passage"):
            groups.setdefault(r["passage"], []).append(r)
    return groups


def needs_figure(group):
    return is_science(group[0]) and not any(r.get("figure") for r in group)


def request_figure(passage, group):
    """One model call; returns (FigureSpec, citation_sentence) or (None, reason)."""
    stems = [r.get("question", "") for r in group]
    data = chat(
        [{"role": "system", "content": SYSTEM},
         {"role": "user", "content": build_user(passage, stems)}],
        temperature=0.7,
        max_tokens=3000,
    )
    if not isinstance(data, dict) or not isinstance(data.get("figure"), dict):
        return None, "response had no figure object"

    f = data["figure"]
    fig = FigureSpec(
        number=1,
        type=f.get("type", "line"),
        caption=f.get("caption", ""),
        spec=f.get("spec", {}),
        alt=f.get("alt", ""),
    )
    errors = fig.validate()
    if errors:
        return None, errors[0]

    sentence = (data.get("citation_sentence") or "").strip()
    if not re.search("(?:Figure|Table)[ ]*1", sentence):
        return None, "citation_sentence does not name Figure 1"
    return fig, sentence


def apply_figure(group, fig, sentence, rendered):
    """Attach the figure to every question in the set and cite it in the passage."""
    passage = group[0]["passage"].rstrip()
    if not re.search("(?:Figure|Table)[ ]*1", passage):
        passage = passage + "\n\n" + sentence
    for r in group:
        r["passage"] = passage
        r["figure"] = rendered
        r["figure_type"] = fig.type
        r["figure_caption"] = fig.caption
        r["figure_alt"] = fig.alt
        r["figure_spec"] = fig.spec


def main(path, limit=None):
    recs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    groups = group_passages(recs)
    todo = [(p, g) for p, g in groups.items() if needs_figure(g)]
    if limit:
        todo = todo[:limit]

    ck_path = path + CK_SUFFIX
    done = set()
    if os.path.exists(ck_path):
        done = set(json.load(open(ck_path, encoding="utf-8")))

    print(f"{len(groups)} passages in {os.path.basename(path)}; "
          f"{len(todo)} need a figure", flush=True)

    added = 0
    for i, (passage, group) in enumerate(todo, 1):
        key = group[0].get("id") or passage[:60]
        if key in done:
            continue
        print(f"[{i}/{len(todo)}] {group[0].get('topic', '')[:52]} ...", flush=True)

        fig = sentence = None
        for attempt in range(2):
            try:
                fig, sentence = request_figure(passage, group)
            except Exception as e:
                print(f"  ERROR: {e}", flush=True)
                fig = None
                break
            if fig is not None:
                break
            print(f"  attempt {attempt + 1} rejected: {sentence}", flush=True)
        if fig is None:
            print("  SKIPPED", flush=True)
            continue

        rendered = fig.render()
        if not rendered:
            print("  SKIPPED (did not render)", flush=True)
            continue

        apply_figure(group, fig, sentence, rendered)
        added += 1
        done.add(key)

        # Rewrite after each success so an interrupted run keeps its progress.
        with open(path, "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(ck_path, "w", encoding="utf-8") as f:
            json.dump(sorted(done), f, ensure_ascii=False)

    print(f"DONE: added a figure to {added} passage(s) in {path}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="workspace jsonl to backfill in place")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    main(args.path, limit=args.limit)
