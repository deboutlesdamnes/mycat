# -*- coding: utf-8 -*-
"""Pull citation-like lines from OCR and vision image records."""
import re


class CitationExtractor:
    CITE_HINTS = re.compile(
        r"Adapted|et al\.|Journal|Proceedings|©|copyright|Vol\.|doi|http|www\.|"
        r"19[5-9]\d|20[0-2]\d|Nature|Science|Cell|Biochem|Chem|Phys|Psychol|"
        r"Medicine|Physiol|Rev\.|Reproduced|permission|Fig\.|supplement|study by|"
        r"researchers?\b",
        re.I,
    )

    def __init__(self, min_len=20):
        self.min_len = min_len

    def _hits_from_lines(self, fn, lines):
        out = []
        for item in lines:
            if isinstance(item, dict):
                t = item.get("text", "").strip()
            else:
                t = (item or "").strip()
            if not t or len(t) <= self.min_len:
                continue
            if self.CITE_HINTS.search(t):
                out.append((fn, t))
        return out

    def extract_from_ocr(self, images):
        """images: list of {"file", "lines": [{text,...}]}. Returns [(file, text)]."""
        out = []
        for img in images:
            out.extend(self._hits_from_lines(img["file"], img.get("lines", [])))
        return out

    def extract_from_vision(self, records):
        """records: list of {"file", "lines", "figures"}. Returns [(file, text)]."""
        out = []
        for rec in records:
            fn = rec.get("file", "")
            out.extend(self._hits_from_lines(fn, rec.get("lines", [])))
            for fig in rec.get("figures") or []:
                desc = fig.get("description", "") or ""
                if desc and self.CITE_HINTS.search(desc):
                    out.append((fn, f"[FIG {fig.get('number')}] {desc[:400]}"))
        return out
