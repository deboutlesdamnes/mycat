# -*- coding: utf-8 -*-
"""Pull study citations referenced in the figures from OCR raw + Claude vision data."""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CITE_HINTS = re.compile(
    r"Adapted|et al\.|Journal|Proceedings|©|copyright|Vol\.|doi|http|www\.|"
    r"19[5-9]\d|20[0-2]\d|Nature|Science|Cell|Biochem|Chem|Phys|Psychol|"
    r"Medicine|Physiol|Rev\.|Reproduced|permission|Fig\.|supplement|study by|"
    r"researchers?\b",
    re.I,
)


def ocr_citations():
    data = json.load(open(r"workspace/ocr_raw.json", encoding="utf-8"))
    hits = []
    for img in data:
        fn = img["file"]
        for ln in img["lines"]:
            t = ln["text"].strip()
            if not t:
                continue
            if CITE_HINTS.search(t) and len(t) > 20:
                hits.append((fn, t))
    return hits


def vision_citations():
    hits = []
    with open(r"workspace/claude_vision.jsonl", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            fn = obj.get("file", "")
            for t in obj.get("lines", []):
                t = (t or "").strip()
                if t and CITE_HINTS.search(t) and len(t) > 20:
                    hits.append((fn, t))
            for fig in obj.get("figures", []):
                desc = fig.get("description", "") or ""
                if CITE_HINTS.search(desc):
                    hits.append((fn, "[FIG " + str(fig.get("number")) + "] " + desc[:400]))
    return hits


def main():
    ocr = ocr_citations()
    vis = vision_citations()
    print(f"OCR citation-like lines: {len(ocr)}")
    print(f"Vision citation-like lines: {len(vis)}")
    print("\n===== OCR =====")
    for fn, t in ocr:
        print(f"- [{fn}] {t}")
    print("\n===== VISION =====")
    for fn, t in vis:
        print(f"- [{fn}] {t}")


if __name__ == "__main__":
    main()
