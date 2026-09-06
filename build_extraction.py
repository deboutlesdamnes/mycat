# -*- coding: utf-8 -*-
"""Group OCR'd screenshots into a clean, de-duplicated question extraction.

Outputs:
  extracted/images_extracted.md   human-readable transcription
  extracted/images_extracted.json structured version
"""
import json
import os
import re
from collections import OrderedDict

RAW = r"workspace/ocr_raw.json"
OUT_MD = r"extracted/images_extracted.md"
OUT_JSON = r"extracted/images_extracted.json"

CITATION_RE = re.compile(
    r"Adapted|AmericanJournal|AssociationofPhysics|physicscourse|pre-medical|All rights reserved"
)


def clean_ws(s):
    return re.sub(r"\s+", " ", s).strip()


def fix_ocr_artifacts(s):
    s = s.strip()
    m = re.match(r"^Question\s*([0-9oO]+)\s*$", s)
    if m:
        num = m.group(1).replace("o", "0").replace("O", "0")
        return f"Question {int(num)}"
    return s


def is_citation(s):
    return bool(CITATION_RE.search(s))


PASSAGE_RE = re.compile(r"^Passage\s+(\d+)\s*\(Questions?\s*(\d+)\s*[-–—]\s*(\d+)\)\s*$", re.I)
QUESTION_RE = re.compile(r"^Question\s*(\d+)\s*$", re.I)
FIGURE_RE = re.compile(r"^Figure\s+(\d+)(?:[.\s]|$)", re.I)
TABLE_RE = re.compile(r"^Table\s+(\d+)(?:[.\s]|$)", re.I)
OPTION_RE = re.compile(r"^[O0○◦（）()：:\s]*([A-Da-d])\s*[.):：]\s*(.*)$")

# Screenshots where the "Question N" header was not captured by OCR (the stem
# starts the image); inject the missing header so the question is numbered.
SYNTHETIC_HEADERS = {
    "Screenshot 2026-08-30 232943.png": "Question 37",
}


def parse_header(line):
    t = clean_ws(fix_ocr_artifacts(line))
    m = PASSAGE_RE.match(t)
    if m:
        return ("passage", {"num": int(m.group(1)), "q0": int(m.group(2)), "q1": int(m.group(3))})
    m = QUESTION_RE.match(t)
    if m:
        return ("question", int(m.group(1)))
    m = FIGURE_RE.match(t)
    if m:
        return ("figure", {"num": int(m.group(1)), "caption": t})
    m = TABLE_RE.match(t)
    if m:
        return ("table", {"num": int(m.group(1)), "caption": t})
    return None


# --------------------------------------------------------------------------- #
# Containers
# --------------------------------------------------------------------------- #
class Passage:
    def __init__(self, num, q0, q1):
        self.num = num
        self.q0 = q0
        self.q1 = q1
        self.lines = []
        self.src = []
        self.figures = OrderedDict()
        self.tables = OrderedDict()
        self.questions = OrderedDict()

    def merge(self, other):
        if len(other.lines) > len(self.lines):
            self.lines = other.lines
        for k, v in other.figures.items():
            if k not in self.figures:
                self.figures[k] = v
            else:
                if len(v["caption"]) > len(self.figures[k]["caption"]):
                    self.figures[k]["caption"] = v["caption"]
                self.figures[k]["src"] = sorted(set(self.figures[k]["src"]) | set(v["src"]))
        for k, v in other.tables.items():
            if k not in self.tables:
                self.tables[k] = v
            elif len(v["rows"]) > len(self.tables[k]["rows"]):
                self.tables[k] = v
        for k, v in other.questions.items():
            if k in self.questions:
                self.questions[k].merge(v)
            else:
                self.questions[k] = v


class Question:
    def __init__(self, num):
        self.num = num
        self.lines = []
        self.src = []
        self.figures = OrderedDict()

    def merge(self, other):
        if len(other.lines) > len(self.lines):
            self.lines = other.lines
        self.src = sorted(set(self.src) | set(other.src))
        for k, v in other.figures.items():
            if k not in self.figures:
                self.figures[k] = v


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


# --------------------------------------------------------------------------- #
# Table reconstruction
# --------------------------------------------------------------------------- #
def _row_is_junk(cells):
    texts = [t.strip() for _, t in cells if t.strip()]
    if not texts:
        return True
    return all(len(t) <= 3 and not re.search(r"\d", t) for t in texts)


def _filtered_rows(rows):
    ordered = sorted(rows, key=lambda r: (r["top"], r["left"]))
    vrows = []
    cur = [ordered[0]]
    for r in ordered[1:]:
        avg_cy = sum(x["cy"] for x in cur) / len(cur)
        if abs(r["cy"] - avg_cy) <= 0.7 * max(r["h"], 8):
            cur.append(r)
        else:
            vrows.append(cur)
            cur = [r]
    vrows.append(cur)

    kept = []
    for cl in vrows:
        cells = sorted([(c["cx"], c["text"]) for c in cl if c["text"].strip()], key=lambda x: x[0])
        if not cells or _row_is_junk(cells):
            continue
        texts = [t for _, t in cells]
        if kept and [t for _, t in kept[-1]] == texts:
            continue
        kept.append(cells)
    return kept


def _rows_to_markdown(cell_rows):
    all_x = sorted(set(round(x) for row in cell_rows for x, _ in row))
    cols = []
    for x in all_x:
        if cols and x - cols[-1][-1] <= 25:
            cols[-1].append(x)
        else:
            cols.append([x])
    col_centers = [sum(c) / len(c) for c in cols]
    ncols = len(col_centers)

    grid = []
    for cells in cell_rows:
        row = [""] * ncols
        for x, t in cells:
            j = min(range(ncols), key=lambda j: abs(col_centers[j] - x))
            row[j] = (row[j] + " " + t).strip() if row[j] else t
        grid.append(row)

    trans = [[grid[r][c] for r in range(len(grid))] for c in range(ncols)]
    keep_cols = [c for c in range(ncols) if any(trans[c][r].strip() for r in range(len(grid)))]
    grid2 = [[grid[r][c] for c in keep_cols] for r in range(len(grid))]

    def esc(s):
        return s.replace("|", "\\|")

    header = grid2[0]
    out = ["| " + " | ".join(esc(c) for c in header) + " |"]
    out.append("|" + "|".join(["---"] * len(header)) + "|")
    for r in grid2[1:]:
        out.append("| " + " | ".join(esc(c) for c in r) + " |")
    return "\n".join(out)


def reconstruct_table(rows):
    """Return (markdown_or_None, filtered_reading_order_lines)."""
    if not rows:
        return None, []
    kept = _filtered_rows(rows)
    if not kept:
        return None, []

    seen = set()
    reading_lines = []
    for cells in kept:
        line = " ".join(t for _, t in cells)
        if line in seen:
            continue
        seen.add(line)
        reading_lines.append(line)

    md = _rows_to_markdown(kept)
    if md:
        header_cells = md.splitlines()[0].strip("|").split("|")
        if len(header_cells) > 6:
            md = None
    return md, reading_lines


# --------------------------------------------------------------------------- #
# Builder
# --------------------------------------------------------------------------- #
def build():
    data = json.load(open(RAW, encoding="utf-8"))
    sections = []
    passages = OrderedDict()
    standalone = OrderedDict()

    cur_passage = None
    cur_question = None
    cur_figure = None
    cur_table = None
    rescan = False

    seen_passage1 = False

    def new_section():
        nonlocal passages, standalone
        passages, standalone = OrderedDict(), OrderedDict()

    for img in data:
        fn = img["file"]
        if fn.startswith("Screenshot 2026-09-01"):
            continue
        lines = img["lines"]
        if fn in SYNTHETIC_HEADERS:
            lines = [{"text": SYNTHETIC_HEADERS[fn], "cx": 0, "cy": 0, "top": 0, "left": 0, "w": 0, "h": 0}] + lines
        for ln in lines:
            text = ln["text"]
            if not text.strip():
                continue
            if is_citation(text):
                continue
            hdr = parse_header(text)
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
                    cur_figure = None
                    cur_table = None
                elif kind == "question":
                    qnum = payload
                    in_passage = cur_passage is not None and cur_passage.q0 <= qnum <= cur_passage.q1
                    existing = None
                    if in_passage and qnum in cur_passage.questions:
                        existing = cur_passage.questions[qnum]
                    elif qnum in standalone:
                        existing = standalone[qnum]

                    if existing is not None:
                        # Re-capture of a question already seen: the new capture
                        # supersedes the previous (partial) capture.
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
                    cur_figure = None
                    cur_table = None
                elif kind == "figure":
                    fnum = payload["num"]
                    if cur_question is not None:
                        target = cur_question.figures
                    elif cur_passage is not None:
                        target = cur_passage.figures
                    else:
                        target = None
                    if target is not None:
                        if fnum in target:
                            if rescan:
                                cur_figure = None
                            else:
                                if len(payload["caption"]) > len(target[fnum]["caption"]):
                                    target[fnum]["caption"] = payload["caption"]
                                if fn not in target[fnum]["src"]:
                                    target[fnum]["src"].append(fn)
                                cur_figure = (target, fnum)
                        else:
                            target[fnum] = {"caption": payload["caption"], "src": [fn]}
                            cur_figure = (target, fnum)
                        cur_table = None
                elif kind == "table":
                    tnum = payload["num"]
                    if cur_passage is not None:
                        if tnum in cur_passage.tables:
                            if rescan:
                                cur_table = None
                            else:
                                if fn not in cur_passage.tables[tnum]["src"]:
                                    cur_passage.tables[tnum]["src"].append(fn)
                                cur_table = (cur_passage, tnum)
                        else:
                            cur_passage.tables[tnum] = {"caption": payload["caption"], "rows": [], "src": [fn]}
                            cur_table = (cur_passage, tnum)
                        cur_figure = None
                continue

            if cur_table is not None:
                cur_table[0].tables[cur_table[1]]["rows"].append(ln)
                continue
            if cur_question is not None:
                cur_question.lines.append(clean_ws(text))
                continue
            if cur_passage is not None and not rescan:
                cur_passage.lines.append(clean_ws(text))
                continue

    sections.append({"passages": passages, "standalone": standalone})
    return sections


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
SECTION_SUBJECTS = [
    "Chemical and Physical Foundations of Biological Systems (Chem/Phys)",
    "Biological and Biochemical Foundations of Living Systems (Bio/Biochem)",
    "Biological and Biochemical Foundations of Living Systems (Bio/Biochem)",
    "Psychological, Social, and Biological Foundations of Behavior (Psych/Soc)",
]


def render_md(sections):
    parts = [
        "# MCAT Question Bank — Extracted from Screenshots (OCR)\n",
        "\n",
        "_Transcribed automatically from 351 screenshots in `images/` using RapidOCR. "
        "Passages, questions, and options are grouped and de-duplicated; split questions are merged. "
        "Figures are listed by caption with their source image file so the original diagrams can be viewed. "
        "Some diagram-based answer choices and a few option letters that OCR could not recover may be incomplete — "
        "refer to the listed source images for those._\n",
    ]
    for si, sec in enumerate(sections):
        if not sec["passages"] and not sec["standalone"]:
            continue
        subject = SECTION_SUBJECTS[si] if si < len(SECTION_SUBJECTS) else f"Section {si + 1}"
        parts.append(f"# Section {si + 1} — {subject}\n")
        for pnum, p in sec["passages"].items():
            parts.append(f"\n## Passage {p.num} (Questions {p.q0}-{p.q1})\n")
            parts.append(f"_Source images: {', '.join(p.src)}_\n")
            if p.lines:
                parts.append("> " + "\n> ".join(p.lines) + "\n")
            for fnum, f in p.figures.items():
                parts.append(f"\n**{f['caption']}**  \n_Source: {', '.join(f['src'])}_\n")
            for tnum, t in p.tables.items():
                cap = t["caption"]
                md, raw_lines = reconstruct_table(t["rows"])
                parts.append(f"\n**{cap}**  \n_Source: {', '.join(t['src'])}_\n")
                use_grid = md and len(t["src"]) == 1
                if use_grid:
                    parts.append(md + "\n")
                else:
                    parts.append("```\n" + "\n".join(raw_lines) + "\n```\n")
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
                    parts.append(f"_(Figure: {f['caption']})_\n")

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
                    parts.append(f"_(Figure: {f['caption']})_\n")
    return "\n".join(parts)


def render_json(sections):
    out = []
    for si, sec in enumerate(sections):
        subject = SECTION_SUBJECTS[si] if si < len(SECTION_SUBJECTS) else f"Section {si + 1}"
        for pnum, p in sec["passages"].items():
            for qnum in sorted(p.questions):
                q = p.questions[qnum]
                stem, opts = split_options(q.lines)
                tables_json = {}
                for tnum, t in p.tables.items():
                    _, raw_lines = reconstruct_table(t["rows"])
                    tables_json[str(tnum)] = {
                        "caption": t["caption"],
                        "source_images": t["src"],
                        "rows": raw_lines,
                    }
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
                    "figures": {str(k): {"caption": v["caption"], "source_images": v["src"]} for k, v in p.figures.items()},
                    "tables": tables_json,
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
                "figures": {str(k): {"caption": v["caption"], "source_images": v["src"]} for k, v in q.figures.items()},
                "tables": {},
            })
    return out


def main():
    sections = build()
    md = render_md(sections)
    js = render_json(sections)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(js, f, ensure_ascii=False, indent=1)
    total_q = 0
    for si, sec in enumerate(sections):
        pq = sum(len(p.questions) for p in sec["passages"].values())
        sq = len(sec["standalone"])
        total_q += pq + sq
        print(f"Section {si+1}: passages={len(sec['passages'])} passage-questions={pq} standalone={sq}")
    print("TOTAL QUESTIONS:", total_q)
    print("WROTE", OUT_MD, "and", OUT_JSON)


if __name__ == "__main__":
    main()
