# -*- coding: utf-8 -*-
"""Extract text from corpus PDF and EPUB files into UTF-8 .txt files."""
import os, zipfile, re, sys
import fitz  # PyMuPDF
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
    for i, page in enumerate(doc):
        parts.append(f"\n===PAGE {i+1}===\n")
        parts.append(page.get_text("text"))
    doc.close()
    return clean("\n".join(parts))

def extract_epub(path):
    z = zipfile.ZipFile(path)
    names = z.namelist()
    # find container.xml to locate OPF
    opf = None
    if "META-INF/container.xml" in names:
        soup = BeautifulSoup(z.read("META-INF/container.xml"), "lxml-xml")
        rootfile = soup.find("rootfile")
        if rootfile:
            opf = rootfile.get("full-path")
    # find spine order from OPF if possible
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
        # fallback: all xhtml/html files sorted
        spine = sorted([n for n in names if re.search(r"\.(x?html?|xml)$", n, re.I)])
    parts = []
    for n in spine:
        if n not in names:
            continue
        try:
            data = z.read(n)
        except Exception as e:
            continue
        soup = BeautifulSoup(data, "lxml")
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text("\n")
        parts.append(f"\n===FILE {n}===\n")
        parts.append(clean(text))
    return clean("\n".join(parts))

def main():
    results = []
    for fn in sorted(os.listdir(CORPUS)):
        path = os.path.join(CORPUS, fn)
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(fn)[1].lower()
        print(f"Processing {fn} ...", flush=True)
        try:
            if ext == ".pdf":
                text = extract_pdf(path)
            elif ext == ".epub":
                text = extract_epub(path)
            else:
                continue
        except Exception as e:
            print(f"  ERROR {fn}: {e}", flush=True)
            results.append((fn, 0, str(e)))
            continue
        outfn = os.path.splitext(fn)[0] + ".txt"
        with open(os.path.join(OUT, outfn), "w", encoding="utf-8") as f:
            f.write(text)
        results.append((fn, len(text), "OK"))
        print(f"  -> {outfn} ({len(text)} chars)", flush=True)
    print("\n===SUMMARY===", flush=True)
    for fn, n, status in results:
        print(f"{fn}: {status} {n} chars", flush=True)

if __name__ == "__main__":
    main()
