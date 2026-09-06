# -*- coding: utf-8 -*-
"""Write a human-readable summary of workspace/research_corpus.json."""
import json
from collections import Counter, defaultdict

data = json.load(open(r"workspace/research_corpus.json", encoding="utf-8"))
CATS = [c for c, _ in []] if False else data["meta"]["categories"]

lines = []
lines.append("# MCAT Research Paper Corpus (OpenAlex)")
lines.append("")
lines.append("Method: top-cited journal articles (`type=article`, `is_retracted=false`, "
             "`has_doi=true`, `primary_location.source.type=journal`) per MCAT science category, "
             "deduplicated by DOI.")
lines.append("")
lines.append(f"- Classics: {len(data['classics'])} papers (all-time most-cited)")
lines.append(f"- Recent:   {len(data['recent'])} papers (published {data['meta']['recent_from']} or later, most-cited)")
lines.append("")


def section(label, papers):
    lines.append(f"## {label} ({len(papers)} papers)")
    lines.append("")
    by_cat = defaultdict(list)
    for p in papers:
        by_cat[p["category"]].append(p)
    for cat in CATS:
        ps = by_cat.get(cat, [])
        years = sorted({p["year"] for p in ps if p["year"]})
        lines.append(f"### {cat} ({len(ps)} papers)")
        for p in ps[:5]:
            fa = p["first_author"] or "?"
            lines.append(f"- **{p['year']}** · {fa} — *{p['title']}* — {p['journal']} "
                         f"(cites {p['citations']:,}, doi:{p['doi']})")
        lines.append("")


section("Classics (all-time most-cited)", data["classics"])
section("Recent (2020+ most-cited)", data["recent"])

with open(r"workspace/research_corpus.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("WROTE workspace/research_corpus.md")
