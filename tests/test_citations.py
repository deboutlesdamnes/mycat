# -*- coding: utf-8 -*-
import unittest

from mcat_extract.citations import CitationExtractor


class TestCitationExtractor(unittest.TestCase):
    def setUp(self):
        self.ext = CitationExtractor()

    def test_ocr_extraction(self):
        images = [{"file": "a.png", "lines": [
            {"text": "Adapted from P. H. Bunton et al., A simple integrated circuit model."},
            {"text": "The axon is surrounded by fluid."},
        ]}]
        hits = self.ext.extract_from_ocr(images)
        self.assertEqual(len(hits), 1)
        self.assertIn("Bunton", hits[0][1])

    def test_vision_extraction_includes_figure_descriptions(self):
        records = [{
            "file": "a.png",
            "lines": ["Adapted from S. Mukhopadhyay and A. Linstedt, Science 2012."],
            "figures": [{"number": 1, "caption": "Fig 1", "description": "Adapted from Nature 2010 study"}],
        }]
        hits = self.ext.extract_from_vision(records)
        self.assertEqual(len(hits), 2)
        self.assertTrue(any("FIG 1" in h[1] for h in hits))

    def test_min_len_filter(self):
        ext = CitationExtractor(min_len=100)
        images = [{"file": "a.png", "lines": [{"text": "Nature"}]}]
        self.assertEqual(ext.extract_from_ocr(images), [])


if __name__ == "__main__":
    unittest.main()
