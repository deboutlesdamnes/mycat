# -*- coding: utf-8 -*-
"""Summarize ocr_raw.json: image order, line counts, first/last lines, time gaps."""
import json
import os
import re
from datetime import datetime

data = json.load(open(r"workspace/ocr_raw.json", encoding="utf-8"))
print("TOTAL IMAGES:", len(data))

# parse timestamps from filename: "Screenshot 2026-08-30 220927.png"
def ts(fn):
    m = re.search(r"(\d{4}-\d{2}-\d{2}) (\d{6})", fn)
    if not m:
        return None
    return datetime.strptime(m.group(1) + m.group(2), "%Y-%m-%d%H%M%S")

prev = None
for i, img in enumerate(data):
    fn = img["file"]
    t = ts(fn)
    gap = ""
    if prev is not None and t is not None:
        gap = f"  gap={int((t - prev).total_seconds())}s"
    lines = img["lines"]
    first = lines[0]["text"] if lines else "(empty)"
    last = lines[-1]["text"] if lines else "(empty)"
    print(f"[{i}] {fn}  n={len(lines)}{gap}")
    print(f"      first: {first[:80]}")
    print(f"      last : {last[:80]}")
    prev = t
