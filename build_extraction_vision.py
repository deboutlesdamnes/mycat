# -*- coding: utf-8 -*-
"""Build the final grouped extraction from Claude vision transcriptions.

Input:  workspace/claude_vision.jsonl  (one JSON object per image)
Output: extracted/images_extracted.md / .json  (overwrites OCR-based version)
"""
import json
import os
import re
from collections import OrderedDict

VISION = r"workspace/claude_vision.jsonl"
OUT_MD = r"extracted/images_extracted.md"
OUT_JSON = r"extracted/images_extracted.json"
OUT_TXT = r"extracted/images_extracted.txt"

PASSAGE_RE = re.compile(r"^Passage\s+(\d+)\s*\(Questions?\s*(\d+)\s*[-–—]\s*(\d+)\)\s*$", re.I)
QUESTION_RE = re.compile(r"^Question\s*(\d+)\s*$", re.I)
FIGURE_RE = re.compile(r"^Figure\s+(\d+)(?:[.\s]|$)", re.I)
TABLE_RE = re.compile(r"^Table\s+(\d+)(?:[.\s]|$)", re.I)
OPTION_RE = re.compile(r"^[O0○◦（）()：:\s]*([A-Da-d])\s*[.):：]\s*(.*)$")

# Screenshots where the "Question N" header is physically absent (captured from
# the stem onward). Only applied if the vision transcript has no such header.
SYNTHETIC_HEADERS = {
    "images/Screenshot 2026-08-30 232943.png": "Question 37",
}


def clean_ws(s):
    return re.sub(r"\s+", " ", s).strip()


def parse_header(line):
    t = clean_ws(line)
    m = PASSAGE_RE.match(t)
    if m:
        return ("passage", {"num": int(m.group(1)), "q0": int(m.group(2)), "q1": int(m.group(3))})
    m = QUESTION_RE.match(t)
    if m:
        return ("question", int(m.group(1)))
    m = FIGURE_RE.match(t)
    if m:
        return ("figure", int(m.group(1)))
    m = TABLE_RE.match(t)
    if m:
        return ("table", int(m.group(1)))
    return None


class Passage:
    def __init__(self, num, q0, q1):
        self.num = num
        self.q0 = q0
        self.q1 = q1
        self.lines = []
        self.src = []
        self.figures = OrderedDict()  # num -> {"caption","description","src":[]}
        self.tables = OrderedDict()   # num -> {"caption","rows":[[...]],"src":[]}
        self.questions = OrderedDict()

    def add_figure(self, num, caption, description, src):
        if num in self.figures:
            f = self.figures[num]
            if len(description or "") > len(f["description"] or ""):
                f["description"] = description
            if len(caption or "") > len(f["caption"] or ""):
                f["caption"] = caption
            if src not in f["src"]:
                f["src"].append(src)
        else:
            self.figures[num] = {"caption": caption, "description": description, "src": [src]}

    def add_table(self, num, caption, rows, src):
        if num in self.tables:
            t = self.tables[num]
            if rows and (not t["rows"] or len(rows) > len(t["rows"])):
                t["rows"] = rows
            if len(caption or "") > len(t["caption"] or ""):
                t["caption"] = caption
            if src not in t["src"]:
                t["src"].append(src)
        else:
            self.tables[num] = {"caption": caption, "rows": rows or [], "src": [src]}


class Question:
    def __init__(self, num):
        self.num = num
        self.lines = []
        self.src = []
        self.figures = OrderedDict()

    def add_figure(self, num, caption, description, src):
        if num in self.figures:
            f = self.figures[num]
            if len(description or "") > len(f["description"] or ""):
                f["description"] = description
            if len(caption or "") > len(f["caption"] or ""):
                f["caption"] = caption
            if src not in f["src"]:
                f["src"].append(src)
        else:
            self.figures[num] = {"caption": caption, "description": description, "src": [src]}


def split_options(lines):
    stem = []
    options = OrderedDict()
    cur = None
    for raw in lines:
        t = clean_ws(raw)
        m = OPTION_RE.match(t)
        if m:
            cur = m.group(1).upper()
            rest = m.group(2).strip()
            options[cur] = [rest] if rest else []
        else:
            if cur is not None:
                options[cur].append(t)
            else:
                stem.append(t)
    while stem and not stem[-1]:
        stem.pop()
    return stem, options


def table_to_markdown(caption, rows):
    if not rows:
        return ""
    out = []
    if caption:
        out.append(f"**{caption}**\n")
    ncols = max(len(r) for r in rows)
    norm = [r + [""] * (ncols - len(r)) for r in rows]
    def esc(s):
        return str(s).replace("|", "\\|")
    out.append("| " + " | ".join(esc(c) for c in norm[0]) + " |")
    out.append("|" + "|".join(["---"] * ncols) + "|")
    for r in norm[1:]:
        out.append("| " + " | ".join(esc(c) for c in r) + " |")
    return "\n".join(out)


def build():
    data = []
    with open(VISION, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    # The fallback path appends individually-processed images at the end of the
    # file; restore chronological order so section detection works.
    data.sort(key=lambda o: o.get("file", ""))

    sections = []
    passages = OrderedDict()
    standalone = OrderedDict()

    cur_passage = None
    cur_question = None
    rescan = False
    seen_passage1 = False

    def new_section():
        nonlocal passages, standalone
        passages, standalone = OrderedDict(), OrderedDict()

    for img in data:
        fn = img.get("file", "")
        if not fn:
            continue
        lines = img.get("lines", [])
        figures = img.get("figures", []) or []
        tables = img.get("tables", []) or []

        # inject synthetic header if the vision transcript lacks it
        if fn in SYNTHETIC_HEADERS:
            has_q = any(parse_header(l) == ("question", int(SYNTHETIC_HEADERS[fn].split()[-1])) for l in lines)
            if not has_q:
                lines = [SYNTHETIC_HEADERS[fn]] + lines

        for text in lines:
            if not text or not text.strip():
                continue
            t = clean_ws(text)
            hdr = parse_header(t)
            if hdr:
                kind, payload = hdr
                if kind == "passage":
                    if payload["num"] == 1 and seen_passage1:
                        sections.append({"passages": passages, "standalone": standalone})
                        new_section()
                    seen_passage1 = True
                    num = payload["num"]
                    if num in passages:
                        passages[num].q0 = min(passages[num].q0, payload["q0"])
                        passages[num].q1 = max(passages[num].q1, payload["q1"])
                        rescan = True
                    else:
                        passages[num] = Passage(num, payload["q0"], payload["q1"])
                        rescan = False
                    if fn not in passages[num].src:
                        passages[num].src.append(fn)
                    cur_passage = passages[num]
                    cur_question = None
                elif kind == "question":
                    qnum = payload
                    in_passage = cur_passage is not None and cur_passage.q0 <= qnum <= cur_passage.q1
                    existing = None
                    if in_passage and qnum in cur_passage.questions:
                        existing = cur_passage.questions[qnum]
                    elif qnum in standalone:
                        existing = standalone[qnum]
                    if existing is not None:
                        existing.lines = []
                        q = existing
                        if in_passage and qnum not in cur_passage.questions:
                            if qnum in standalone:
                                del standalone[qnum]
                            cur_passage.questions[qnum] = q
                    else:
                        q = Question(qnum)
                        if in_passage:
                            cur_passage.questions[qnum] = q
                        else:
                            standalone[qnum] = q
                    if fn not in q.src:
                        q.src.append(fn)
                    cur_question = q
                    rescan = False
                elif kind in ("figure", "table"):
                    # captions in the text are rendered from the structured
                    # figures/tables lists below, so skip the caption line.
                    continue
                continue

            # route non-header text
            if cur_question is not None:
                cur_question.lines.append(t)
            elif cur_passage is not None and not rescan:
                cur_passage.lines.append(t)

        # attach this image's structured figures/tables to the active context
        for f in figures:
            try:
                fnum = int(f.get("number"))
            except (TypeError, ValueError):
                continue
            cap = f.get("caption", "")
            desc = f.get("description", "")
            if cur_question is not None:
                cur_question.add_figure(fnum, cap, desc, fn)
            elif cur_passage is not None:
                cur_passage.add_figure(fnum, cap, desc, fn)
        for t in tables:
            try:
                tnum = int(t.get("number"))
            except (TypeError, ValueError):
                continue
            cap = t.get("caption", "")
            rows = t.get("rows", []) or []
            if cur_question is not None:
                # rare: table inside a question
                pass
            elif cur_passage is not None:
                cur_passage.add_table(tnum, cap, rows, fn)

    sections.append({"passages": passages, "standalone": standalone})
    return sections


SECTION_SUBJECTS = [
    "Chemical and Physical Foundations of Biological Systems (Chem/Phys)",
    "Critical Analysis and Reasoning Skills (CARS)",
    "Biological and Biochemical Foundations of Living Systems (Bio/Biochem)",
    "Psychological, Social, and Biological Foundations of Behavior (Psych/Soc)",
]


def render_md(sections):
    parts = [
        "# MCAT Question Bank — Extracted from Screenshots (Claude Vision)\n",
        "\n",
        "_Transcribed from 351 screenshots in `images/` using the Claude vision model. "
        "Passages, questions, and options are grouped and de-duplicated; split questions are merged. "
        "Figures include a detailed description; tables are transcribed as markdown. "
        "Source image filenames are listed for cross-reference._\n",
    ]
    for si, sec in enumerate(sections):
        if not sec["passages"] and not sec["standalone"]:
            continue
        subject = SECTION_SUBJECTS[si] if si < len(SECTION_SUBJECTS) else f"Section {si + 1}"
        parts.append(f"\n# Section {si + 1} — {subject}\n")
        for pnum, p in sec["passages"].items():
            parts.append(f"\n## Passage {p.num} (Questions {p.q0}-{p.q1})\n")
            parts.append(f"_Source images: {', '.join(p.src)}_\n")
            if p.lines:
                parts.append("> " + "\n> ".join(p.lines) + "\n")
            for fnum, f in p.figures.items():
                cap = f["caption"] or f"Figure {fnum}"
                parts.append(f"\n**{cap}**  \n_Source: {', '.join(f['src'])}_\n")
                if f["description"]:
                    parts.append(f"> _{f['description']}_\n")
            for tnum, t in p.tables.items():
                md = table_to_markdown(t["caption"] or f"Table {tnum}", t["rows"])
                parts.append(f"\n_Source: {', '.join(t['src'])}_\n")
                if md:
                    parts.append(md + "\n")
            for qnum in sorted(p.questions):
                q = p.questions[qnum]
                stem, opts = split_options(q.lines)
                parts.append(f"\n### Question {q.num}\n")
                parts.append(f"_Source images: {', '.join(q.src)}_\n")
                if stem:
                    parts.append(" ".join(stem) + "\n")
                for letter in ["A", "B", "C", "D"]:
                    if letter in opts:
                        parts.append(f"- **{letter}.** " + " ".join(opts[letter]) + "\n")
                for fnum, f in q.figures.items():
                    parts.append(f"_(Figure {fnum}: {f['caption']} — {f['description']})_\n")

        if sec["standalone"]:
            parts.append(f"\n## Standalone Questions\n")
            for qnum in sorted(sec["standalone"]):
                q = sec["standalone"][qnum]
                stem, opts = split_options(q.lines)
                parts.append(f"\n### Question {q.num}\n")
                parts.append(f"_Source images: {', '.join(q.src)}_\n")
                if stem:
                    parts.append(" ".join(stem) + "\n")
                for letter in ["A", "B", "C", "D"]:
                    if letter in opts:
                        parts.append(f"- **{letter}.** " + " ".join(opts[letter]) + "\n")
                for fnum, f in q.figures.items():
                    parts.append(f"_(Figure {fnum}: {f['caption']} — {f['description']})_\n")
    return "\n".join(parts)


def render_json(sections):
    out = []
    for si, sec in enumerate(sections):
        subject = SECTION_SUBJECTS[si] if si < len(SECTION_SUBJECTS) else f"Section {si + 1}"
        for pnum, p in sec["passages"].items():
            for qnum in sorted(p.questions):
                q = p.questions[qnum]
                stem, opts = split_options(q.lines)
                out.append({
                    "section": si + 1,
                    "subject": subject,
                    "kind": "passage",
                    "passage": p.num,
                    "passage_question_range": [p.q0, p.q1],
                    "question": q.num,
                    "passage_text": "\n".join(p.lines),
                    "question_text": " ".join(stem),
                    "options": {k: " ".join(v) for k, v in opts.items()},
                    "source_images": p.src + q.src,
                    "figures": {str(k): {"caption": v["caption"], "description": v["description"], "source_images": v["src"]} for k, v in p.figures.items()},
                    "tables": {str(k): {"caption": v["caption"], "rows": v["rows"], "source_images": v["src"]} for k, v in p.tables.items()},
                })
        for qnum in sorted(sec["standalone"]):
            q = sec["standalone"][qnum]
            stem, opts = split_options(q.lines)
            out.append({
                "section": si + 1,
                "subject": subject,
                "kind": "standalone",
                "passage": None,
                "passage_question_range": None,
                "question": q.num,
                "passage_text": "",
                "question_text": " ".join(stem),
                "options": {k: " ".join(v) for k, v in opts.items()},
                "source_images": q.src,
                "figures": {str(k): {"caption": v["caption"], "description": v["description"], "source_images": v["src"]} for k, v in q.figures.items()},
                "tables": {},
            })
    return out


def render_txt(sections):
    """Plain-text rendering for the retrieval corpus (extracted/*.txt)."""
    parts = ["MCAT Question Bank - Extracted from Screenshots (Claude Vision)"]
    for si, sec in enumerate(sections):
        if not sec["passages"] and not sec["standalone"]:
            continue
        subject = SECTION_SUBJECTS[si] if si < len(SECTION_SUBJECTS) else f"Section {si + 1}"
        parts.append(f"\nSECTION {si + 1} - {subject}")
        for pnum, p in sec["passages"].items():
            parts.append(f"\nPASSAGE {p.num} (Questions {p.q0}-{p.q1})")
            if p.lines:
                parts.append("\n".join(p.lines))
            for fnum, f in p.figures.items():
                parts.append(f"\nFIGURE {fnum}: {f['caption']}")
                if f["description"]:
                    parts.append(f["description"])
            for tnum, t in p.tables.items():
                parts.append(f"\nTABLE {tnum}: {t['caption']}")
                for row in t["rows"]:
                    parts.append(" | ".join(str(c) for c in row))
            for qnum in sorted(p.questions):
                q = p.questions[qnum]
                stem, opts = split_options(q.lines)
                parts.append(f"\nQUESTION {q.num}")
                parts.append(" ".join(stem))
                for letter in ["A", "B", "C", "D"]:
                    if letter in opts:
                        parts.append(f"{letter}. " + " ".join(opts[letter]))
                for fnum, f in q.figures.items():
                    parts.append(f"[Figure {fnum}: {f['caption']} - {f['description']}]")
        if sec["standalone"]:
            parts.append("\nSTANDALONE QUESTIONS")
            for qnum in sorted(sec["standalone"]):
                q = sec["standalone"][qnum]
                stem, opts = split_options(q.lines)
                parts.append(f"\nQUESTION {q.num}")
                parts.append(" ".join(stem))
                for letter in ["A", "B", "C", "D"]:
                    if letter in opts:
                        parts.append(f"{letter}. " + " ".join(opts[letter]))
                for fnum, f in q.figures.items():
                    parts.append(f"[Figure {fnum}: {f['caption']} - {f['description']}]")
    return "\n".join(parts)


def main():
    sections = build()
    md = render_md(sections)
    js = render_json(sections)
    txt = render_txt(sections)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(js, f, ensure_ascii=False, indent=1)
    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write(txt + "\n")
    total_q = 0
    for si, sec in enumerate(sections):
        pq = sum(len(p.questions) for p in sec["passages"].values())
        sq = len(sec["standalone"])
        total_q += pq + sq
        print(f"Section {si+1}: passages={len(sec['passages'])} passage-questions={pq} standalone={sq}")
    print("TOTAL QUESTIONS:", total_q)
    print("WROTE", OUT_MD, OUT_JSON, "and", OUT_TXT)


if __name__ == "__main__":
    main()
