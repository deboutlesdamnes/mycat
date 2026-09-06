# -*- coding: utf-8 -*-
"""Thin wrapper around the Claude Code CLI for vision transcription."""
import json
import os
import re
import subprocess


class ClaudeCliClient:
    PROMPT_TEMPLATE = (
        "You are transcribing MCAT exam screenshots for a question bank. "
        "Read each image file listed below and return ONLY a valid JSON array with one "
        "object per image, in the same order. Each object must have exactly these keys:\n"
        '  "file": the image path string exactly as given,\n'
        '  "lines": array of strings, every text line exactly as it appears, in top-to-bottom '
        "reading order (keep chemistry notation, units, and option letters A-D exact),\n"
        '  "figures": array of {{"number": int, "caption": str, "description": str}} for any '
        "diagram, graph, or chemical structure (describe it in detail: axes, labels, trends, "
        "chemical groups, stereochemistry),\n"
        '  "tables": array of {{"number": int, "caption": str, "rows": [[cell, ...], ...]}} for '
        "any table (rows is a list of cell lists; include the header row).\n"
        "Do not add prose outside the JSON. Image files:\n"
        "{paths}"
    )

    def __init__(self, executable=None, cwd=None, allowed_tools=("Read",)):
        self.executable = executable or os.environ.get("CLAUDE_BIN") or "claude"
        self.cwd = cwd
        self.allowed_tools = list(allowed_tools)

    def build_prompt(self, paths):
        return self.PROMPT_TEMPLATE.format(paths="\n".join(paths))

    def run(self, prompt, timeout=900):
        """Run the CLI in print mode and return the subprocess result."""
        env = os.environ.copy()
        # Empty (not missing) key prevents Claude Code from reading a no-credit
        # ANTHROPIC_API_KEY from .env, so it falls back to the claude.ai login.
        env["ANTHROPIC_API_KEY"] = ""
        cmd = [self.executable, "-p", prompt, "--allowedTools", ",".join(self.allowed_tools), "--output-format", "json"]
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout,
            cwd=self.cwd,
        )

    @staticmethod
    def parse_result(stdout):
        """Parse the JSON envelope from `claude -p --output-format json`."""
        envelope = json.loads(stdout)
        result = envelope.get("result", "")
        text = result if isinstance(result, str) else json.dumps(result)
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)
