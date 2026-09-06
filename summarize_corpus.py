# -*- coding: utf-8 -*-
"""Validate and summarize workspace/research_corpus.json."""
import json
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = json.load(open(r"workspace/research_corpus.json", encoding="utf-8"))


def stats(papers, label):
    dois = [p["doi"] for p in papers]
    years = [p["year"] for p in papers if p["year"]]
    cites = [p["citations"] for p in papers if p["citations"] is not None]
    by_cat = Counter(p["category"] for p in papers)
    journals = Counter(p["journal"] for p in papers)
    print(f"\n=== {label}: {len(papers)} papers ===")
    print(f"unique DOIs: {len(set(dois))}")
    print(f"year range: {min(years)} - {max(years)}")
    print(f"citations: min={min(cites)} max={max(cites)} median={sorted(cites)[len(cites)//2]}")
    print("per category:", dict(by_cat))
    print("top journals:", journals.most_common(8))
    print("sample entries:")
    for p in papers[:3]:
        print(f"  [{p['year']}] {p['first_author']} | {p['title'][:70]} | {p['journal']} | {p['doi']}")


stats(data["classics"], "CLASSICS")
stats(data["recent"], "RECENT")

# cross-tier DOI overlap (same paper appearing as both classic and recent)
c_dois = {p["doi"] for p in data["classics"]}
r_dois = {p["doi"] for p in data["recent"]}
print("\ncross-tier DOI overlap:", len(c_dois & r_dois))
