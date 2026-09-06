# -*- coding: utf-8 -*-
import unittest

from mcat_extract.text import (
    clean_ws,
    fix_ocr_artifacts,
    is_citation,
    HeaderParser,
    split_options,
)


class TestClean(unittest.TestCase):
    def test_clean_ws_collapses(self):
        self.assertEqual(clean_ws("  a   b\tc  "), "a b c")

    def test_fix_ocr_question_headers(self):
        self.assertEqual(fix_ocr_artifacts("Question 1o"), "Question 10")
        self.assertEqual(fix_ocr_artifacts("Question3o"), "Question 30")
        self.assertEqual(fix_ocr_artifacts("Question5o"), "Question 50")
        self.assertEqual(fix_ocr_artifacts("Question 1"), "Question 1")

    def test_is_citation(self):
        self.assertTrue(is_citation("Adapted from P. H. Bunton et al."))
        self.assertTrue(is_citation("American Journal of Physics. 1996"))
        self.assertFalse(is_citation("The axon is surrounded by fluid."))


class TestHeaderParser(unittest.TestCase):
    def setUp(self):
        self.parser = HeaderParser()

    def test_passage(self):
        self.assertEqual(self.parser.parse("Passage 2 (Questions 5-9)"),
                         ("passage", {"num": 2, "q0": 5, "q1": 9}))

    def test_passage_singular_question(self):
        self.assertEqual(self.parser.parse("Passage 4 (Question 20-25)"),
                         ("passage", {"num": 4, "q0": 20, "q1": 25}))

    def test_question(self):
        self.assertEqual(self.parser.parse("Question 7"), ("question", 7))
        self.assertEqual(self.parser.parse("Question 1o"), ("question", 10))

    def test_figure(self):
        self.assertEqual(self.parser.parse("Figure 1 The peptide bond")[0], "figure")
        self.assertEqual(self.parser.parse("Figure 1 The peptide bond")[1]["num"], 1)

    def test_table(self):
        self.assertEqual(self.parser.parse("Table 2")[0], "table")

    def test_none(self):
        self.assertIsNone(self.parser.parse("This is ordinary text."))


class TestSplitOptions(unittest.TestCase):
    def test_plain_options(self):
        stem, opts = split_options([
            "Which is correct?",
            "A. one",
            "B. two",
            "C. three",
            "D. four",
        ])
        self.assertEqual(stem, ["Which is correct?"])
        self.assertEqual(list(opts.keys()), ["A", "B", "C", "D"])
        self.assertEqual(opts["A"], ["one"])

    def test_ocr_variants(self):
        stem, opts = split_options([
            "Pick one:",
            "O A. first",
            ") B. second",
            "0C. third",
            "）D. fourth",
        ])
        self.assertEqual(list(opts.keys()), ["A", "B", "C", "D"])

    def test_lowercase_option(self):
        stem, opts = split_options(["Stem", "c. lowercase"])
        self.assertIn("C", opts)
        self.assertEqual(opts["C"], ["lowercase"])

    def test_continuation_lines_attach_to_option(self):
        stem, opts = split_options(["Stem", "A. long option", "continued here"])
        self.assertEqual(opts["A"], ["long option", "continued here"])

    def test_stem_without_options(self):
        stem, opts = split_options(["Just a stem."])
        self.assertEqual(stem, ["Just a stem."])
        self.assertEqual(opts, {})


if __name__ == "__main__":
    unittest.main()
