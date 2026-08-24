# -*- coding: utf-8 -*-
"""Extract full text from every corpus PDF/EPUB into extracted/*.txt.

Uses whole-document text extraction for PDFs (much faster than per-page),
skips files that were already extracted, and logs progress.
"""
import os
import zipfile
import re

import fitz
from bs4 import BeautifulSoup

CORPUS = r"c:\Users\jason\Documents\mycat\corpus"
OUT = r"c:\Users\jason\Documents\mycat\extracted"
os.makedirs(OUT, exist_ok=True)


def clean(text):
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf(path):
    doc = fitz.open(path)
    parts = []
    n = doc.page_count
    for i in range(n):
        parts.append(f"\n===PAGE {i + 1}===\n")
        parts.append(doc[i].get_text("text"))
        if (i + 1) % 200 == 0:
            print(f"    {os.path.basename(path)}: page {i + 1}/{n}", flush=True)
    doc.close()
    return clean("\n".join(parts))


def extract_epub(path):
    z = zipfile.ZipFile(path)
    names = z.namelist()
    opf = None
    if "META-INF/container.xml" in names:
        soup = BeautifulSoup(z.read("META-INF/container.xml"), "lxml-xml")
        rootfile = soup.find("rootfile")
        if rootfile:
            opf = rootfile.get("full-path")
    spine = []
    if opf and opf in names:
        soup = BeautifulSoup(z.read(opf), "lxml-xml")
        for itemref in soup.find_all("itemref"):
            idref = itemref.get("idref")
            for item in soup.find_all("item"):
                if item.get("id") == idref:
                    href = item.get("href")
                    base = os.path.dirname(opf)
                    full = os.path.normpath(os.path.join(base, href)).replace("\\", "/")
                    spine.append(full)
    if not spine:
        spine = sorted([n for n in names if re.search(r"\.(x?html?|xml)$", n, re.I)])
    parts = []
    for n in spine:
        if n not in names:
            continue
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


def main():
    for fn in sorted(os.listdir(CORPUS)):
        path = os.path.join(CORPUS, fn)
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(fn)[1].lower()
        outfn = os.path.join(OUT, os.path.splitext(fn)[0] + ".txt")
        if os.path.exists(outfn) and os.path.getsize(outfn) > 0:
            print(f"SKIP {fn} (already extracted)", flush=True)
            continue
        print(f"START {fn}", flush=True)
        try:
            if ext == ".pdf":
                text = extract_pdf(path)
            elif ext == ".epub":
                text = extract_epub(path)
            else:
                continue
        except Exception as e:
            print(f"ERROR {fn}: {e}", flush=True)
            continue
        with open(outfn, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"DONE {fn} -> {os.path.basename(outfn)} ({len(text)} chars)", flush=True)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
