# -*- coding: utf-8 -*-
"""Build a research-paper corpus from OpenAlex.

- 500 "classics": all-time most-cited journal articles per MCAT science category.
- 500 "recent": most-cited journal articles published 2020 or later per category.

Categories (MCAT science sections, excluding CARS): Biology, Biochemistry,
General Chemistry, Organic Chemistry, Physics, Psychology, Sociology.

Output: workspace/research_corpus.json
"""
import json
import re
import time

import requests

BASE = "https://api.openalex.org"
MAILTO = "research-corpus@example.com"
HEADERS = {"User-Agent": f"mycat-research-corpus/1.0 (mailto:{MAILTO})"}

CATEGORIES = [
    ("Biology", "C86803240"),
    ("Biochemistry", "C55493867"),
    ("General Chemistry", "C185592680"),
    ("Organic Chemistry", "C178790620"),
    ("Physics", "C121332964"),
    ("Psychology", "C15744967"),
    ("Sociology", "C144024400"),
]

PER_CATEGORY = 72          # 7 * 72 = 504, trimmed to 500
RECENT_FROM = "2020-01-01"
SELECT = "id,doi,title,publication_year,cited_by_count,primary_location,authorships,type"

# Drop software/tool/database/statistics-tool titles and obvious citation-count
# glitches so the corpus skews toward actual findings/studies.
EXCLUDE_TITLE = re.compile(
    r"\b(software|package|database|webserver|web\s*server|server|suite|tool|tools|"
    r"protocol|benchmark|manual|user\s*guide)\b|"
    r"cutoff criteria|fit indexes|cancer statistics|camera system|visualization system|"
    r"\bversion\s*\d",
    re.I,
)
MAX_CITATIONS = 500000


def fetch_works(concept_id, from_year, page, per_page=100):
    filters = [
        f"concepts.id:{concept_id}",
        "type:article",
        "is_retracted:false",
        "has_doi:true",
        "primary_location.source.type:journal",
    ]
    if from_year:
        filters.append(f"from_publication_date:{from_year}")
    url = (
        f"{BASE}/works"
        f"?filter={','.join(filters)}"
        f"&sort=cited_by_count:desc"
        f"&per-page={per_page}&page={page}"
        f"&select={SELECT}"
    )
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.json()


def parse_work(w):
    src = ((w.get("primary_location") or {}).get("source") or {})
    first = ""
    auths = w.get("authorships") or []
    if auths:
        first = (auths[0].get("author") or {}).get("display_name", "")
    return {
        "title": (w.get("title") or "").strip(),
        "year": w.get("publication_year"),
        "journal": src.get("display_name", ""),
        "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
        "citations": w.get("cited_by_count"),
        "first_author": first,
    }


def collect_category(category, concept_id, from_year, seen, needed, max_pages=8):
    """Fetch top-cited works for one category, skipping DOIs already in `seen`
    and dropping software/tool/database titles and citation-count glitches."""
    out = []
    for page in range(1, max_pages + 1):
        data = fetch_works(concept_id, from_year, page)
        results = data.get("results", [])
        if not results:
            break
        for w in results:
            p = parse_work(w)
            doi = p["doi"]
            if not doi or doi in seen:
                continue
            if EXCLUDE_TITLE.search(p["title"]):
                continue
            if p["citations"] is not None and p["citations"] > MAX_CITATIONS:
                continue
            seen.add(doi)
            p["category"] = category
            out.append(p)
            if len(out) >= needed:
                return out
        time.sleep(0.2)
    return out


def build_tier(from_year, label, total=500):
    seen = set()
    corpus = []
    # first pass: one share per category
    for category, cid in CATEGORIES:
        corpus.extend(collect_category(category, cid, from_year, seen, PER_CATEGORY))
        print(f"  {label}: {category} -> cumulative {len(corpus)}", flush=True)
    # second pass to top up categories that fell short (e.g. heavy dedup)
    if len(corpus) < total:
        for category, cid in CATEGORIES:
            remaining = total - len(corpus)
            if remaining <= 0:
                break
            extra = collect_category(category, cid, from_year, seen, remaining)
            corpus.extend(extra)
            print(f"  {label}: top-up {category} +{len(extra)} -> cumulative {len(corpus)}", flush=True)
    return corpus[:total]


def main():
    print("Pulling classics (all-time top-cited)...", flush=True)
    classics = build_tier(None, "classics")
    print(f"Classics: {len(classics)}", flush=True)

    print("Pulling recent (2020+) top-cited...", flush=True)
    recent = build_tier(RECENT_FROM, "recent")
    print(f"Recent: {len(recent)}", flush=True)

    out = {
        "meta": {
            "source": "OpenAlex",
            "method": "top-cited journal articles (type=article, is_retracted=false, has_doi=true)",
            "categories": [c for c, _ in CATEGORIES],
            "classics_count": len(classics),
            "recent_count": len(recent),
            "recent_from": RECENT_FROM,
        },
        "classics": classics,
        "recent": recent,
    }
    with open(r"workspace/research_corpus.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("WROTE workspace/research_corpus.json", flush=True)


if __name__ == "__main__":
    main()
