# -*- coding: utf-8 -*-
import unittest

from mcat_extract.models import Passage, Question, Section


class TestQuestion(unittest.TestCase):
    def test_merge_keeps_longer(self):
        q1 = Question(5)
        q1.lines = ["stem", "A. a"]
        q2 = Question(5)
        q2.lines = ["stem", "A. a", "B. b", "C. c", "D. d"]
        q1.merge(q2)
        self.assertEqual(q1.lines, q2.lines)

    def test_merge_unions_src(self):
        q1 = Question(5)
        q1.src = ["a.png"]
        q2 = Question(5)
        q2.src = ["b.png"]
        q1.merge(q2)
        self.assertEqual(q1.src, ["a.png", "b.png"])

    def test_add_figure(self):
        q = Question(1)
        q.add_figure(1, "Fig 1", "a diagram", "x.png")
        q.add_figure(1, "Fig 1 longer caption", "short", "y.png")
        self.assertEqual(q.figures[1]["caption"], "Fig 1 longer caption")
        self.assertEqual(q.figures[1]["description"], "a diagram")
        self.assertEqual(q.figures[1]["src"], ["x.png", "y.png"])


class TestPassage(unittest.TestCase):
    def test_add_table_rows(self):
        p = Passage(1, 1, 4)
        p.add_table(1, "T", [["a", "b"], ["c", "d"]], None, "x.png")
        p.add_table(1, "T2", [], None, "y.png")
        self.assertEqual(p.tables[1]["caption"], "T2")
        self.assertEqual(p.tables[1]["rows"], [["a", "b"], ["c", "d"]])
        self.assertEqual(p.tables[1]["src"], ["x.png", "y.png"])

    def test_merge_questions(self):
        p1 = Passage(1, 1, 4)
        p2 = Passage(1, 1, 4)
        p1.questions[1] = Question(1)
        p2.questions[2] = Question(2)
        p1.merge(p2)
        self.assertEqual(sorted(p1.questions), [1, 2])


class TestSection(unittest.TestCase):
    def test_counts(self):
        sec = Section()
        p = Passage(1, 1, 2)
        p.questions[1] = Question(1)
        p.questions[2] = Question(2)
        sec.passages[1] = p
        sec.standalone[3] = Question(3)
        self.assertEqual(sec.passage_questions(), 2)
        self.assertEqual(sec.total_questions(), 3)


if __name__ == "__main__":
    unittest.main()
