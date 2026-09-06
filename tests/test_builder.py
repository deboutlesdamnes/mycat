# -*- coding: utf-8 -*-
import unittest

from mcat_extract.builder import SectionBuilder


def ocr_record(file, lines):
    rec_lines = [
        {"text": t, "cx": cx, "cy": cy, "top": cy, "left": cx, "h": 10}
        for (t, cx, cy) in lines
    ]
    return {"file": file, "mode": "ocr", "lines": rec_lines, "figures": [], "tables": []}


def vision_record(file, lines, figures=None, tables=None):
    return {"file": file, "mode": "vision", "lines": lines, "figures": figures or [], "tables": tables or []}


class TestSectionBuilder(unittest.TestCase):
    def test_section_reset_on_second_passage1(self):
        b = SectionBuilder()
        b.feed(vision_record("a.png", ["Passage 1 (Questions 1-2)", "text", "Question 1", "A. x", "Question 2", "A. y"]))
        b.feed(vision_record("b.png", ["Passage 1 (Questions 1-2)", "text2", "Question 1", "A. z"]))
        sections = b.finish()
        self.assertEqual(len(sections), 2)

    def test_passage_vs_standalone_question(self):
        b = SectionBuilder()
        b.feed(vision_record("p.png", ["Passage 1 (Questions 1-2)", "text", "Question 1", "A. x"]))
        b.feed(vision_record("q.png", ["Question 5", "stem", "A. a", "B. b"]))
        sections = b.finish()
        sec = sections[0]
        self.assertEqual(list(sec.passages[1].questions), [1])
        self.assertEqual(list(sec.standalone), [5])

    def test_question_recapture_moves_to_passage(self):
        b = SectionBuilder()
        b.feed(vision_record("q40a.png", ["Question 40", "partial", "A. x"]))
        b.feed(vision_record("p8.png", ["Passage 8 (Questions 40-43)", "passage text"]))
        b.feed(vision_record("q40b.png", ["Question 40", "full stem", "A. a", "B. b", "C. c", "D. d"]))
        sections = b.finish()
        sec = sections[0]
        self.assertNotIn(40, sec.standalone)
        q = sec.passages[8].questions[40]
        self.assertIn("full stem", q.lines)
        self.assertEqual(len(q.lines), 5)  # stem + 4 options

    def test_ocr_table_normalized(self):
        b = SectionBuilder()
        b.feed(ocr_record("p.png", [("Passage 1 (Questions 1-2)", 100, 10)]))
        b.feed(ocr_record("t.png", [
            ("Table 1", 100, 10),
            ("Property", 100, 30), ("Nonmyelinated", 300, 30), ("Myelinated", 500, 30),
            ("Axon radius", 100, 50), ("5 x 10-6 m", 300, 50), ("5 x 10-6 m", 500, 50),
        ]))
        sections = b.finish()
        t = sections[0].passages[1].tables[1]
        self.assertIsInstance(t["rows"][0], list)
        self.assertIn("markdown", t)
        self.assertIn("Nonmyelinated", t["markdown"])

    def test_vision_figure_table_attach(self):
        b = SectionBuilder()
        b.feed(vision_record(
            "p.png",
            ["Passage 1 (Questions 1-2)", "text"],
            figures=[{"number": 1, "caption": "Fig 1", "description": "a graph"}],
            tables=[{"number": 1, "caption": "Table 1", "rows": [["A", "B"], ["1", "2"]]}],
        ))
        sections = b.finish()
        p = sections[0].passages[1]
        self.assertEqual(p.figures[1]["description"], "a graph")
        self.assertEqual(p.tables[1]["rows"], [["A", "B"], ["1", "2"]])

    def test_synthetic_question_header(self):
        b = SectionBuilder(synthetic_headers={"img/x.png": "Question 37"})
        b.feed(vision_record("img/x.png", ["Passage 7 (Questions 36-39)", "Question 36", "A. a"]))
        b.feed(vision_record("img/x.png", ["stem text without header", "A. a", "B. b"]))
        # Note: same file twice; first feed creates Q36, second injects Q37 before stem
        sections = b.finish()
        qs = sections[0].passages[7].questions
        self.assertIn(37, qs)
        self.assertIn("stem text without header", qs[37].lines)

    def test_citation_lines_skipped(self):
        b = SectionBuilder()
        b.feed(vision_record("p.png", ["Passage 1 (Questions 1-2)", "Adapted from Someone et al.", "real text"]))
        sections = b.finish()
        self.assertEqual(sections[0].passages[1].lines, ["real text"])


if __name__ == "__main__":
    unittest.main()
