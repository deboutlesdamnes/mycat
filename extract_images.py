# -*- coding: utf-8 -*-
"""OCR every screenshot in images/ and dump structured results to workspace/ocr_raw.json.

Each image becomes:
    {
      "file": "...",
      "width": int, "height": int,
      "lines": [ {"text": str, "score": float, "cx": float, "cy": float,
                  "top": float, "left": float, "w": float, "h": float}, ... ]
    }
Lines are sorted into reading order (top-to-bottom, then left-to-right within a line).
"""
import json
import os
import re

from rapidocr_onnxruntime import RapidOCR

IMG = r"c:\Users\jason\Documents\mycat\images"
OUT = r"c:\Users\jason\Documents\mycat\workspace\ocr_raw.json"

engine = RapidOCR()


def sort_key(blocks):
    """Sort blocks into reading order using a y-clustering pass."""
    if not blocks:
        return blocks
    # sort by top edge
    ordered = sorted(blocks, key=lambda b: (b["top"], b["left"]))
    lines = []
    cur = [ordered[0]]
    for b in ordered[1:]:
        # same line if vertical overlap with the running line's average cy
        avg_cy = sum(x["cy"] for x in cur) / len(cur)
        avg_h = sum(x["h"] for x in cur) / len(cur)
        if abs(b["cy"] - avg_cy) <= 0.6 * max(avg_h, b["h"], 8):
            cur.append(b)
        else:
            lines.append(sorted(cur, key=lambda x: x["left"]))
            cur = [b]
    lines.append(sorted(cur, key=lambda x: x["left"]))
    return [b for line in lines for b in line]


def main():
    files = sorted(
        [f for f in os.listdir(IMG) if f.lower().endswith(".png")],
        key=lambda f: f,
    )
    out = []
    for i, fn in enumerate(files):
        path = os.path.join(IMG, fn)
        result, _ = engine(path)
        blocks = []
        if result:
            for box, text, score in result:
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                x1, x2 = min(xs), max(xs)
                y1, y2 = min(ys), max(ys)
                blocks.append({
                    "text": text.strip(),
                    "score": round(float(score), 4),
                    "cx": round((x1 + x2) / 2, 1),
                    "cy": round((y1 + y2) / 2, 1),
                    "top": round(y1, 1),
                    "left": round(x1, 1),
                    "w": round(x2 - x1, 1),
                    "h": round(y2 - y1, 1),
                })
        from PIL import Image
        im = Image.open(path)
        w, h = im.size
        out.append({
            "file": fn,
            "width": w,
            "height": h,
            "lines": sort_key(blocks),
        })
        print(f"[{i + 1}/{len(files)}] {fn} -> {len(blocks)} blocks", flush=True)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("WROTE", OUT, "| images:", len(out))


if __name__ == "__main__":
    main()
