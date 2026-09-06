# -*- coding: utf-8 -*-
"""SectionBuilder: group OCR or vision image records into sections/passages/questions."""
from collections import OrderedDict

from .text import HeaderParser, clean_ws, is_citation, fix_ocr_artifacts
from .models import Passage, Question, Section
from .tables import TableReconstructor

# Screenshots where the "Question N" header is physically absent; a synthetic
# header is injected so the question is still numbered.
SYNTHETIC_HEADERS = {
    "images/Screenshot 2026-08-30 232943.png": "Question 37",
}


class SectionBuilder:
    def __init__(self, synthetic_headers=None):
        self.parser = HeaderParser()
        self.synthetic_headers = synthetic_headers if synthetic_headers is not None else dict(SYNTHETIC_HEADERS)
        self.sections = []
        self.passages = OrderedDict()
        self.standalone = OrderedDict()
        self.cur_passage = None
        self.cur_question = None
        self.cur_table = None   # (Passage, tnum) for OCR coordinate collection
        self.rescan = False
        self.seen_passage1 = False

    def _new_section(self):
        self.sections.append(Section(self.passages, self.standalone))
        self.passages = OrderedDict()
        self.standalone = OrderedDict()

    def _handle_passage(self, payload, fn):
        if payload["num"] == 1 and self.seen_passage1:
            self._new_section()
        self.seen_passage1 = True
        num = payload["num"]
        if num in self.passages:
            self.passages[num].q0 = min(self.passages[num].q0, payload["q0"])
            self.passages[num].q1 = max(self.passages[num].q1, payload["q1"])
            self.rescan = True
        else:
            self.passages[num] = Passage(num, payload["q0"], payload["q1"])
            self.rescan = False
        if fn not in self.passages[num].src:
            self.passages[num].src.append(fn)
        self.cur_passage = self.passages[num]
        self.cur_question = None
        self.cur_table = None

    def _handle_question(self, qnum, fn):
        in_passage = self.cur_passage is not None and self.cur_passage.q0 <= qnum <= self.cur_passage.q1
        existing = None
        if in_passage and qnum in self.cur_passage.questions:
            existing = self.cur_passage.questions[qnum]
        elif qnum in self.standalone:
            existing = self.standalone[qnum]

        if existing is not None:
            # Re-capture of a question already seen: the newer capture supersedes.
            existing.lines = []
            q = existing
            if in_passage and qnum not in self.cur_passage.questions:
                if qnum in self.standalone:
                    del self.standalone[qnum]
                self.cur_passage.questions[qnum] = q
        else:
            q = Question(qnum)
            if in_passage:
                self.cur_passage.questions[qnum] = q
            else:
                self.standalone[qnum] = q

        if fn not in q.src:
            q.src.append(fn)
        self.cur_question = q
        self.rescan = False
        self.cur_table = None

    def _handle_figure(self, fnum, caption, fn):
        if self.cur_question is not None:
            self.cur_question.add_figure(fnum, caption, "", fn)
        elif self.cur_passage is not None:
            self.cur_passage.add_figure(fnum, caption, "", fn)
        self.cur_table = None

    def feed(self, record):
        """Feed one image record.

        record keys:
          file    str
          mode    'ocr' | 'vision'
          lines   for vision: list[str]; for OCR: list[dict] with text + coords
          figures list (vision structured figures)
          tables  list (vision structured tables)
        """
        fn = record["file"]
        mode = record["mode"]
        raw_lines = record["lines"]

        # synthetic header injection (vision only)
        if mode == "vision" and fn in self.synthetic_headers:
            synthetic = self.synthetic_headers[fn]
            qnum = int(synthetic.split()[-1])
            already = any(
                self.parser.parse(clean_ws(fix_ocr_artifacts(l))) == ("question", qnum)
                for l in raw_lines if isinstance(l, str)
            )
            if not already:
                self._handle_question(qnum, fn)

        for raw_line in raw_lines:
            if isinstance(raw_line, dict):
                text = raw_line.get("text", "").strip()
                coord = raw_line
            else:
                text = raw_line.strip()
                coord = None
            if not text:
                continue
            if is_citation(text):
                continue

            hdr = self.parser.parse(text)
            if hdr:
                kind, payload = hdr
                if kind == "passage":
                    self._handle_passage(payload, fn)
                elif kind == "question":
                    self._handle_question(payload, fn)
                elif kind == "figure":
                    if mode == "ocr":
                        self._handle_figure(payload["num"], payload["caption"], fn)
                    else:
                        self.cur_table = None
                elif kind == "table":
                    if mode == "ocr" and self.cur_passage is not None:
                        self.cur_passage.add_table(payload["num"], payload["caption"], [], None, fn)
                        self.cur_table = (self.cur_passage, payload["num"])
                    else:
                        self.cur_table = None
                continue

            t = clean_ws(text)
            if self.cur_table is not None and mode == "ocr":
                self.cur_table[0].tables[self.cur_table[1]]["rows"].append(coord or t)
                continue
            if self.cur_question is not None:
                self.cur_question.lines.append(t)
            elif self.cur_passage is not None and not self.rescan:
                self.cur_passage.lines.append(t)

        # vision: attach structured figures/tables to the active context
        if mode == "vision":
            for f in record.get("figures") or []:
                try:
                    fnum = int(f.get("number"))
                except (TypeError, ValueError):
                    continue
                if self.cur_question is not None:
                    self.cur_question.add_figure(fnum, f.get("caption", ""), f.get("description", ""), fn)
                elif self.cur_passage is not None:
                    self.cur_passage.add_figure(fnum, f.get("caption", ""), f.get("description", ""), fn)
            for t in record.get("tables") or []:
                try:
                    tnum = int(t.get("number"))
                except (TypeError, ValueError):
                    continue
                if self.cur_passage is not None:
                    self.cur_passage.add_table(tnum, t.get("caption", ""), t.get("rows") or [], None, fn)

    def finish(self):
        """Finalize, normalize OCR tables, and return the list of Sections."""
        self.sections.append(Section(self.passages, self.standalone))
        rec = TableReconstructor()
        for sec in self.sections:
            for p in sec.passages.values():
                for tnum, t in p.tables.items():
                    rows = t.get("rows") or []
                    if rows and isinstance(rows[0], dict):  # OCR coordinate rows
                        md, reading = rec.reconstruct(rows)
                        t["rows"] = [[line] for line in reading]
                        if md:
                            t["markdown"] = md
        return self.sections
