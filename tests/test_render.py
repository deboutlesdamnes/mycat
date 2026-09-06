# -*- coding: utf-8 -*-
import unittest

from mcat_extract.models import Passage, Question, Section
from mcat_extract.render import Renderer


def build_section():
    sec = Section()
    p = Passage(1, 1, 2)
    p.lines = ["Passage text."]
    p.src = ["p.png"]
    p.add_figure(1, "Fig 1", "a diagram", "p.png")
    p.add_table(1, "Table 1", [["A", "B"], ["1", "2"]], None, "p.png")
    q1 = Question(1)
    q1.lines = ["Which one?", "A. first", "B. second", "C. third", "D. fourth"]
    p.questions[1] = q1
    sec.passages[1] = p
    sec.standalone[5] = Question(5)
    sec.standalone[5].lines = ["Standalone stem", "A. a", "B. b", "C. c", "D. d"]
    return [sec]


class TestRenderer(unittest.TestCase):
    def setUp(self):
        self.r = Renderer(build_section())

    def test_markdown(self):
        md = self.r.to_markdown()
        self.assertIn("# Section 1 — Chemical and Physical", md)
        self.assertIn("## Passage 1 (Questions 1-2)", md)
        self.assertIn("> Passage text.", md)
        self.assertIn("**Fig 1**", md)
        self.assertIn("a diagram", md)
        self.assertIn("| A | B |", md)
        self.assertIn("### Question 1", md)
        self.assertIn("Standalone stem", md)

    def test_json(self):
        records = self.r.to_json()
        self.assertEqual(len(records), 2)
        passage_rec = [r for r in records if r["kind"] == "passage"][0]
        self.assertEqual(passage_rec["passage"], 1)
        self.assertEqual(passage_rec["options"], {"A": "first", "B": "second", "C": "third", "D": "fourth"})
        self.assertEqual(passage_rec["figures"]["1"]["description"], "a diagram")

    def test_text(self):
        txt = self.r.to_text()
        self.assertIn("PASSAGE 1 (Questions 1-2)", txt)
        self.assertIn("QUESTION 1", txt)
        self.assertIn("A. first", txt)


if __name__ == "__main__":
    unittest.main()
