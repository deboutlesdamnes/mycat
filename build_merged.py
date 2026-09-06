# -*- coding: utf-8 -*-
"""Build a full UTF-8 merged transcript of all OCR'd images with image markers."""
import json

data = json.load(open(r"workspace/ocr_raw.json", encoding="utf-8"))
parts = []
for i, img in enumerate(data):
    parts.append(f"\n===== IMAGE {i:03d} | {img['file']} | {img['width']}x{img['height']} =====\n")
    for ln in img["lines"]:
        parts.append(ln["text"])
out = "\n".join(parts) + "\n"
with open(r"workspace/ocr_merged.txt", "w", encoding="utf-8") as f:
    f.write(out)
print("WROTE workspace/ocr_merged.txt", len(out), "chars,", len(data), "images")
