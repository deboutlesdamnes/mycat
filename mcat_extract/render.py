# -*- coding: utf-8 -*-
"""Render Sections to Markdown, JSON, and plain text."""
from .text import split_options
from .tables import table_to_markdown

SECTION_SUBJECTS = [
    "Chemical and Physical Foundations of Biological Systems (Chem/Phys)",
    "Critical Analysis and Reasoning Skills (CARS)",
    "Biological and Biochemical Foundations of Living Systems (Bio/Biochem)",
    "Psychological, Social, and Biological Foundations of Behavior (Psych/Soc)",
]


class Renderer:
    def __init__(self, sections, subjects=None):
        self.sections = sections
        self.subjects = subjects if subjects is not None else SECTION_SUBJECTS

    def _subject(self, si):
        return self.subjects[si] if si < len(self.subjects) else f"Section {si + 1}"

    def _render_question(self, q):
        stem, opts = split_options(q.lines)
        return {
            "stem": " ".join(stem),
            "options": {k: " ".join(v) for k, v in opts.items()},
            "figures": q.figures,
        }

    def to_markdown(self):
        parts = [
            "# MCAT Question Bank — Extracted from Screenshots\n",
            "\n",
            "_Passages, questions, and options are grouped and de-duplicated; split questions "
            "are merged. Figures include descriptions; tables are transcribed as markdown._\n",
        ]
        for si, sec in enumerate(self.sections):
            if not sec.passages and not sec.standalone:
                continue
            parts.append(f"\n# Section {si + 1} — {self._subject(si)}\n")
            for pnum, p in sec.passages.items():
                parts.append(f"\n## Passage {p.num} (Questions {p.q0}-{p.q1})\n")
                parts.append(f"_Source images: {', '.join(p.src)}_\n")
                if p.lines:
                    parts.append("> " + "\n> ".join(p.lines) + "\n")
                for fnum, f in p.figures.items():
                    cap = f["caption"] or f"Figure {fnum}"
                    parts.append(f"\n**{cap}**  \n_Source: {', '.join(f.get('src', []))}_\n")
                    if f.get("description"):
                        parts.append(f"> _{f['description']}_\n")
                for tnum, t in p.tables.items():
                    md = t.get("markdown") or table_to_markdown(t.get("caption") or f"Table {tnum}", t.get("rows") or [])
                    parts.append(f"\n_Source: {', '.join(t.get('src', []))}_\n")
                    if md:
                        parts.append(md + "\n")
                for qnum in sorted(p.questions):
                    q = p.questions[qnum]
                    r = self._render_question(q)
                    parts.append(f"\n### Question {q.num}\n")
                    parts.append(f"_Source images: {', '.join(q.src)}_\n")
                    if r["stem"]:
                        parts.append(r["stem"] + "\n")
                    for letter in ["A", "B", "C", "D"]:
                        if letter in r["options"]:
                            parts.append(f"- **{letter}.** {r['options'][letter]}\n")
                    for fnum, f in q.figures.items():
                        parts.append(f"_(Figure {fnum}: {f['caption']} — {f.get('description','')})_\n")
            if sec.standalone:
                parts.append("\n## Standalone Questions\n")
                for qnum in sorted(sec.standalone):
                    q = sec.standalone[qnum]
                    r = self._render_question(q)
                    parts.append(f"\n### Question {q.num}\n")
                    parts.append(f"_Source images: {', '.join(q.src)}_\n")
                    if r["stem"]:
                        parts.append(r["stem"] + "\n")
                    for letter in ["A", "B", "C", "D"]:
                        if letter in r["options"]:
                            parts.append(f"- **{letter}.** {r['options'][letter]}\n")
                    for fnum, f in q.figures.items():
                        parts.append(f"_(Figure {fnum}: {f['caption']} — {f.get('description','')})_\n")
        return "\n".join(parts)

    def to_json(self):
        out = []
        for si, sec in enumerate(self.sections):
            subject = self._subject(si)
            for pnum, p in sec.passages.items():
                for qnum in sorted(p.questions):
                    q = p.questions[qnum]
                    r = self._render_question(q)
                    out.append({
                        "section": si + 1,
                        "subject": subject,
                        "kind": "passage",
                        "passage": p.num,
                        "passage_question_range": [p.q0, p.q1],
                        "question": q.num,
                        "passage_text": "\n".join(p.lines),
                        "question_text": r["stem"],
                        "options": r["options"],
                        "source_images": p.src + q.src,
                        "figures": {str(k): {"caption": v["caption"], "description": v.get("description", ""), "source_images": v.get("src", [])} for k, v in p.figures.items()},
                        "tables": {str(k): {"caption": v.get("caption", ""), "rows": v.get("rows", []), "source_images": v.get("src", [])} for k, v in p.tables.items()},
                    })
            for qnum in sorted(sec.standalone):
                q = sec.standalone[qnum]
                r = self._render_question(q)
                out.append({
                    "section": si + 1,
                    "subject": subject,
                    "kind": "standalone",
                    "passage": None,
                    "passage_question_range": None,
                    "question": q.num,
                    "passage_text": "",
                    "question_text": r["stem"],
                    "options": r["options"],
                    "source_images": q.src,
                    "figures": {str(k): {"caption": v["caption"], "description": v.get("description", ""), "source_images": v.get("src", [])} for k, v in q.figures.items()},
                    "tables": {},
                })
        return out

    def to_text(self):
        parts = ["MCAT Question Bank - Extracted from Screenshots"]
        for si, sec in enumerate(self.sections):
            if not sec.passages and not sec.standalone:
                continue
            parts.append(f"\nSECTION {si + 1} - {self._subject(si)}")
            for pnum, p in sec.passages.items():
                parts.append(f"\nPASSAGE {p.num} (Questions {p.q0}-{p.q1})")
                if p.lines:
                    parts.append("\n".join(p.lines))
                for fnum, f in p.figures.items():
                    parts.append(f"\nFIGURE {fnum}: {f['caption']}")
                    if f.get("description"):
                        parts.append(f["description"])
                for tnum, t in p.tables.items():
                    parts.append(f"\nTABLE {tnum}: {t.get('caption','')}")
                    for row in t.get("rows") or []:
                        parts.append(" | ".join(str(c) for c in row))
                for qnum in sorted(p.questions):
                    q = p.questions[qnum]
                    r = self._render_question(q)
                    parts.append(f"\nQUESTION {q.num}")
                    parts.append(r["stem"])
                    for letter in ["A", "B", "C", "D"]:
                        if letter in r["options"]:
                            parts.append(f"{letter}. {r['options'][letter]}")
            if sec.standalone:
                parts.append("\nSTANDALONE QUESTIONS")
                for qnum in sorted(sec.standalone):
                    q = sec.standalone[qnum]
                    r = self._render_question(q)
                    parts.append(f"\nQUESTION {q.num}")
                    parts.append(r["stem"])
                    for letter in ["A", "B", "C", "D"]:
                        if letter in r["options"]:
                            parts.append(f"{letter}. {r['options'][letter]}")
        return "\n".join(parts)
