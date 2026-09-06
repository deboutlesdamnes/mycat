# -*- coding: utf-8 -*-
"""OpenAlex client, Paper model, and citation-ranked corpus builder."""
import re
import time
from dataclasses import dataclass, field, asdict


@dataclass
class Paper:
    title: str
    year: int
    journal: str
    doi: str
    citations: int
    first_author: str
    category: str = ""

    def to_dict(self):
        return asdict(self)


class OpenAlexClient:
    BASE = "https://api.openalex.org"
    SELECT = "id,doi,title,publication_year,cited_by_count,primary_location,authorships,type"

    def __init__(self, mailto="research-corpus@example.com"):
        self.headers = {"User-Agent": f"mycat-research-corpus/1.0 (mailto:{mailto})"}

    def fetch_works(self, concept_id, from_year, page, per_page=100, session=None):
        import requests

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
            f"{self.BASE}/works?filter={','.join(filters)}"
            f"&sort=cited_by_count:desc&per-page={per_page}&page={page}&select={self.SELECT}"
        )
        get = session.get if session else None
        if get:
            r = get(url, headers=self.headers, timeout=60)
        else:
            import requests as _r

            r = _r.get(url, headers=self.headers, timeout=60)
        r.raise_for_status()
        return r.json()

    def parse_work(self, w):
        src = ((w.get("primary_location") or {}).get("source") or {})
        first = ""
        auths = w.get("authorships") or []
        if auths:
            first = (auths[0].get("author") or {}).get("display_name", "")
        return Paper(
            title=(w.get("title") or "").strip(),
            year=w.get("publication_year"),
            journal=src.get("display_name", ""),
            doi=(w.get("doi") or "").replace("https://doi.org/", ""),
            citations=w.get("cited_by_count"),
            first_author=first,
        )


class CorpusBuilder:
    # Drop software/tool/database/statistics-tool titles and citation-count glitches.
    EXCLUDE_TITLE = re.compile(
        r"\b(software|package|database|webserver|web\s*server|server|suite|tool|tools|"
        r"protocol|benchmark|manual|user\s*guide)\b|"
        r"cutoff criteria|fit indexes|cancer statistics|camera system|visualization system|"
        r"\bversion\s*\d",
        re.I,
    )
    MAX_CITATIONS = 500000

    def __init__(self, client=None, categories=None, per_category=72, recent_from="2020-01-01"):
        self.client = client or OpenAlexClient()
        self.categories = categories or [
            ("Biology", "C86803240"),
            ("Biochemistry", "C55493867"),
            ("General Chemistry", "C185592680"),
            ("Organic Chemistry", "C178790620"),
            ("Physics", "C121332964"),
            ("Psychology", "C15744967"),
            ("Sociology", "C144024400"),
        ]
        self.per_category = per_category
        self.recent_from = recent_from

    def _accept(self, paper):
        if not paper.doi:
            return False
        if self.EXCLUDE_TITLE.search(paper.title):
            return False
        if paper.citations is not None and paper.citations > self.MAX_CITATIONS:
            return False
        return True

    def collect_category(self, category, concept_id, from_year, seen, needed, session=None, max_pages=8):
        out = []
        for page in range(1, max_pages + 1):
            data = self.client.fetch_works(concept_id, from_year, page, session=session)
            results = data.get("results", [])
            if not results:
                break
            for w in results:
                paper = self.client.parse_work(w)
                if not self._accept(paper) or paper.doi in seen:
                    continue
                seen.add(paper.doi)
                paper.category = category
                out.append(paper)
                if len(out) >= needed:
                    return out
            time.sleep(0.2)
        return out

    def build_tier(self, from_year, total=500, session=None):
        seen = set()
        corpus = []
        for category, cid in self.categories:
            corpus.extend(self.collect_category(category, cid, from_year, seen, self.per_category, session=session))
        if len(corpus) < total:
            for category, cid in self.categories:
                remaining = total - len(corpus)
                if remaining <= 0:
                    break
                corpus.extend(self.collect_category(category, cid, from_year, seen, remaining, session=session))
        return corpus[:total]

    def build(self, session=None):
        classics = self.build_tier(None, session=session)
        recent = self.build_tier(self.recent_from, session=session)
        return {"classics": [p.to_dict() for p in classics], "recent": [p.to_dict() for p in recent]}
