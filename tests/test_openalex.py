# -*- coding: utf-8 -*-
import unittest

from mcat_extract.openalex import Paper, OpenAlexClient, CorpusBuilder


WORK = {
    "title": "A Landmark Study",
    "publication_year": 2001,
    "primary_location": {"source": {"display_name": "Nature"}},
    "doi": "https://doi.org/10.1234/abc",
    "cited_by_count": 5000,
    "authorships": [{"author": {"display_name": "Jane Doe"}}],
}


class FakeClient:
    def __init__(self, results):
        self.results = results  # list of work dicts
        self.calls = 0

    def fetch_works(self, concept_id, from_year, page, per_page=100, session=None):
        self.calls += 1
        if page == 1:
            return {"results": self.results}
        return {"results": []}

    def parse_work(self, w):
        return OpenAlexClient().parse_work(w)


class TestOpenAlexClient(unittest.TestCase):
    def test_parse_work(self):
        p = OpenAlexClient().parse_work(WORK)
        self.assertEqual(p.title, "A Landmark Study")
        self.assertEqual(p.year, 2001)
        self.assertEqual(p.journal, "Nature")
        self.assertEqual(p.doi, "10.1234/abc")
        self.assertEqual(p.first_author, "Jane Doe")

    def test_parse_work_missing_fields(self):
        p = OpenAlexClient().parse_work({"title": None})
        self.assertEqual(p.title, "")
        self.assertIsNone(p.year)
        self.assertEqual(p.first_author, "")


class TestCorpusBuilder(unittest.TestCase):
    def test_accept_rejects_software_title(self):
        b = CorpusBuilder()
        self.assertFalse(b._accept(Paper("A software package", 2020, "J", "10.1/x", 10, "A")))
        self.assertTrue(b._accept(Paper("A real finding", 2020, "J", "10.1/x", 10, "A")))

    def test_accept_rejects_citation_glitch(self):
        b = CorpusBuilder()
        self.assertFalse(b._accept(Paper("A finding", 2020, "J", "10.1/x", 900000, "A")))

    def test_accept_rejects_missing_doi(self):
        b = CorpusBuilder()
        self.assertFalse(b._accept(Paper("A finding", 2020, "J", "", 10, "A")))

    def test_collect_category_dedup_and_category(self):
        client = FakeClient([WORK, WORK])
        b = CorpusBuilder(client=client)
        out = b.collect_category("Biology", "C1", None, set(), 10, session=None)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].category, "Biology")

    def test_build_tier_respects_total(self):
        client = FakeClient([dict(WORK, doi=f"https://doi.org/10.1/{i}") for i in range(20)])
        b = CorpusBuilder(client=client, categories=[("Biology", "C1")], per_category=5)
        tier = b.build_tier(None, total=5, session=None)
        self.assertEqual(len(tier), 5)


if __name__ == "__main__":
    unittest.main()
