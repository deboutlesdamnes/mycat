# -*- coding: utf-8 -*-
import unittest

from gen_passage_config import (
    build_passage_plan,
    validate_plan,
    passage_question_count,
    discrete_question_count,
    CHEM,
    BIO,
    PSYCH,
    CARS,
)


class TestPassagePlan(unittest.TestCase):
    def setUp(self):
        self.plan = build_passage_plan()
        self.psec = {}
        self.dsec = {}
        for p in self.plan["passages"]:
            self.psec[p["section"]] = self.psec.get(p["section"], 0) + p["n"]
        for d in self.plan["discrete"]:
            self.dsec[d["section"]] = self.dsec.get(d["section"], 0) + d["n"]

    def test_plan_validates_clean(self):
        self.assertEqual(validate_plan(), [])

    def test_totals(self):
        self.assertEqual(passage_question_count(), 185)
        self.assertEqual(discrete_question_count(), 45)
        self.assertEqual(passage_question_count() + discrete_question_count(), 230)

    def test_passages_are_majority(self):
        self.assertGreater(passage_question_count(), discrete_question_count())

    def test_science_sections(self):
        for sec in (CHEM, BIO, PSYCH):
            self.assertEqual(self.psec.get(sec, 0), 44)
            self.assertEqual(self.dsec.get(sec, 0), 15)

    def test_cars_section(self):
        self.assertEqual(self.psec.get(CARS, 0), 53)
        self.assertEqual(self.dsec.get(CARS, 0), 0)

    def test_every_passage_in_range(self):
        for p in self.plan["passages"]:
            self.assertTrue(4 <= p["n"] <= 7, p)

    def test_discrete_counts_positive(self):
        for d in self.plan["discrete"]:
            self.assertGreaterEqual(d["n"], 1)


if __name__ == "__main__":
    unittest.main()
