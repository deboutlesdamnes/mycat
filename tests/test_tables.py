# -*- coding: utf-8 -*-
import unittest

from mcat_extract.tables import TableReconstructor, table_to_markdown


def row(text, cx, cy, top=0, left=0, h=10):
    return {"text": text, "cx": cx, "cy": cy, "top": top, "left": left, "h": h}


class TestTableReconstructor(unittest.TestCase):
    def setUp(self):
        self.rec = TableReconstructor()

    def test_clean_3_col_table(self):
        rows = [
            row("Property", 100, 10, 0, 80),
            row("Nonmyelinated", 300, 10, 0, 280),
            row("Myelinated", 500, 10, 0, 480),
            row("Axon radius", 100, 30, 20, 80),
            row("5 x 10-6 m", 300, 30, 20, 280),
            row("5 x 10-6 m", 500, 30, 20, 480),
        ]
        md, lines = self.rec.reconstruct(rows)
        self.assertIsNotNone(md)
        self.assertIn("Property", md)
        self.assertIn("| Nonmyelinated | Myelinated |", md)
        self.assertEqual(len(lines), 2)

    def test_junk_rows_removed(self):
        rows = [
            row("Property", 100, 10, 0, 80),
            row("Nonmyelinated", 300, 10, 0, 280),
            row("Ri", 100, 30, 20, 80),
            row("Rm", 300, 30, 20, 280),
        ]
        md, lines = self.rec.reconstruct(rows)
        self.assertIsNotNone(md)
        self.assertNotIn("Ri", md)

    def test_wide_table_falls_back_to_none(self):
        rows = [row(f"col{i}", i * 50, 0, 0, i * 50) for i in range(9)]
        md, lines = self.rec.reconstruct(rows)
        self.assertIsNone(md)
        self.assertTrue(lines)

    def test_empty(self):
        md, lines = self.rec.reconstruct([])
        self.assertIsNone(md)
        self.assertEqual(lines, [])


class TestTableToMarkdown(unittest.TestCase):
    def test_render(self):
        md = table_to_markdown("Table 1", [["A", "B"], ["1", "2"]])
        self.assertIn("**Table 1**", md)
        self.assertIn("| A | B |", md)
        self.assertIn("| 1 | 2 |", md)

    def test_ragged_rows_padded(self):
        md = table_to_markdown(None, [["A", "B"], ["1"]])
        self.assertIn("| 1 |  |", md)

    def test_empty(self):
        self.assertEqual(table_to_markdown("T", []), "")


if __name__ == "__main__":
    unittest.main()
