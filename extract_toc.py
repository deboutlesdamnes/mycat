# -*- coding: utf-8 -*-
"""Extract only the table-of-contents / front-matter region of each corpus file."""
import os, zipfile, re
import fitz
from bs4 import BeautifulSoup

CORPUS = r"c:\Users\jason\Documents\mycat\corpus"
OUT = r"c:\Users\jason\Documents\mycat\toc"
os.makedirs(OUT, exist_ok=True)

def clean(text):
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def pdf_toc(path, max_pages=30):
    doc = fitz.open(path)
    parts = []
    n = min(max_pages, doc.page_count)
    for i in range(n):
        parts.append(f"\n===PAGE {i+1}===\n")
        parts.append(doc[i].get_text("text"))
    doc.close()
    return clean("\n".join(parts))

def epub_toc(path):
    z = zipfile.ZipFile(path)
    names = z.namelist()
    # Prefer nav / toc files
    cands = [n for n in names if re.search(r"(nav|toc|contents)\.(x?html?|ncx)$", n, re.I)]
    if not cands:
        cands = [n for n in names if re.search(r"\.(x?html?)$", n, re.I)][:6]
    parts = []
    for n in cands:
        try:
            data = z.read(n)
        except Exception:
            continue
        soup = BeautifulSoup(data, "lxml")
        for tag in soup(["script", "style"]):
            tag.decompose()
        parts.append(f"\n===FILE {n}===\n")
        parts.append(clean(soup.get_text("\n")))
    return clean("\n".join(parts))

for fn in sorted(os.listdir(CORPUS)):
    path = os.path.join(CORPUS, fn)
    if not os.path.isfile(path):
        continue
    ext = os.path.splitext(fn)[1].lower()
    try:
        if ext == ".pdf":
            text = pdf_toc(path)
        elif ext == ".epub":
            text = epub_toc(path)
        else:
            continue
    except Exception as e:
        print(f"ERROR {fn}: {e}", flush=True)
        continue
    outfn = os.path.splitext(fn)[0] + ".txt"
    with open(os.path.join(OUT, outfn), "w", encoding="utf-8") as f:
        f.write(text)
    print(f"{fn} -> {outfn} ({len(text)} chars)", flush=True)

print("DONE", flush=True)
