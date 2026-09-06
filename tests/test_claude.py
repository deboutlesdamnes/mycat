# -*- coding: utf-8 -*-
import json
import unittest

from mcat_extract.claude import ClaudeCliClient


class TestClaudeCliClient(unittest.TestCase):
    def test_build_prompt_includes_paths(self):
        c = ClaudeCliClient(executable="claude")
        prompt = c.build_prompt(["images/a.png", "images/b.png"])
        self.assertIn("images/a.png", prompt)
        self.assertIn("images/b.png", prompt)
        self.assertIn("JSON array", prompt)

    def test_parse_result_strips_fences(self):
        result = json.dumps([{"file": "a.png", "lines": ["x"]}])
        envelope = json.dumps({"result": "```json\n" + result + "\n```"})
        parsed = ClaudeCliClient.parse_result(envelope)
        self.assertEqual(parsed, [{"file": "a.png", "lines": ["x"]}])

    def test_parse_result_no_fences(self):
        result = json.dumps({"a": 1})
        envelope = json.dumps({"result": result})
        self.assertEqual(ClaudeCliClient.parse_result(envelope), {"a": 1})


if __name__ == "__main__":
    unittest.main()
