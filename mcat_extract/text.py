# -*- coding: utf-8 -*-
"""Text cleaning, OCR-artifact fixing, header detection, and option splitting."""
import re
from collections import OrderedDict

CITATION_RE = re.compile(
    r"Adapted|American\s*Journal|Association\s*of\s*Physics|physics\s*course|pre-medical|All rights reserved"
)

PASSAGE_RE = re.compile(r"^Passage\s+(\d+)\s*\(Questions?\s*(\d+)\s*[-–—]\s*(\d+)\)\s*$", re.I)
QUESTION_RE = re.compile(r"^Question\s*(\d+)\s*$", re.I)
FIGURE_RE = re.compile(r"^Figure\s+(\d+)(?:[.\s]|$)", re.I)
TABLE_RE = re.compile(r"^Table\s+(\d+)(?:[.\s]|$)", re.I)
OPTION_RE = re.compile(r"^[O0○◦（）()：:\s]*([A-Da-d])\s*[.):：]\s*(.*)$")


def clean_ws(s):
    return re.sub(r"\s+", " ", s).strip()


def fix_ocr_artifacts(s):
    """Normalize common OCR misreads (e.g. 'Question 1o' -> 'Question 10')."""
    s = s.strip()
    m = re.match(r"^Question\s*([0-9oO]+)\s*$", s)
    if m:
        num = m.group(1).replace("o", "0").replace("O", "0")
        return f"Question {int(num)}"
    return s


def is_citation(s):
    return bool(CITATION_RE.search(s))


class HeaderParser:
    """Detect passage/question/figure/table header lines.

    Returns a (kind, payload) tuple or None. Kinds:
      'passage' -> {"num", "q0", "q1"}
      'question' -> int
      'figure'  -> {"num", "caption"}
      'table'   -> {"num", "caption"}
    """

    def parse(self, line):
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


def split_options(lines):
    """Split a question's accumulated lines into (stem, options).

    Handles OCR option-letter variants such as 'O A.', ') B.', '0C.', and 'c.'.
    """
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
