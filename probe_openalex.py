# -*- coding: utf-8 -*-
"""Probe OpenAlex API: concept lookup + one works query."""
import json
import sys
import urllib.request
import urllib.parse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://api.openalex.org"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "mycat-research-corpus/1.0 (mailto:test@example.com)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


# 1) concept lookup
for term in ["biology", "biochemistry", "chemistry", "organic chemistry", "physics", "psychology", "sociology"]:
    url = BASE + "/concepts?search=" + urllib.parse.quote(term) + "&per-page=3"
    data = get(url)
    print(f"CONCEPT search '{term}':")
    for c in data.get("results", []):
        print(f"   {c['id']}  {c['display_name']}  level={c.get('level')} works={c.get('works_count')}")
    print()

# 2) one works query: top-cited biochemistry articles all time
url = (BASE + "/works?filter=concepts.id:C55493867,type:article"
       "&sort=cited_by_count:desc&per-page=5&select=id,title,publication_year,cited_by_count,primary_location,doi")
data = get(url)
print("WORKS probe (biochemistry C55493867):")
for w in data.get("results", []):
    src = (w.get("primary_location") or {}).get("source") or {}
    print(f"   {w['publication_year']} | cites={w['cited_by_count']} | {src.get('display_name')} | {w['title'][:70]}")
