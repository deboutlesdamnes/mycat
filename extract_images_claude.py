# -*- coding: utf-8 -*-
"""Extract text + figure/table structure from every screenshot using the Claude
Code CLI (vision), in batches. Resumable: skips files already in the output.

Writes one JSON object per image (NDJSON) to workspace/claude_vision.jsonl:
  {"file": "...", "lines": [...], "figures": [...], "tables": [...]}
"""
import json
import os
import re
import subprocess
import time

IMG = r"c:\Users\jason\Documents\mycat\images"
OUT = r"c:\Users\jason\Documents\mycat\workspace\claude_vision.jsonl"
BATCH_SIZE = 8
CLAUDE = r"C:\Users\jason\.local\bin\claude.exe"

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


def load_done():
    done = {}
    if os.path.exists(OUT):
        with open(OUT, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    done[obj["file"]] = obj
                except json.JSONDecodeError:
                    continue
    return done


def run_claude(prompt):
    env = os.environ.copy()
    # Empty (not missing) key prevents Claude Code from reading the no-credit
    # ANTHROPIC_API_KEY out of .env, so it falls back to the claude.ai login.
    env["ANTHROPIC_API_KEY"] = ""
    cmd = [CLAUDE, "-p", prompt, "--allowedTools", "Read", "--output-format", "json"]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=900,
        cwd=r"c:\Users\jason\Documents\mycat",
    )


def parse_result(stdout):
    env = json.loads(stdout)
    result = env.get("result", "")
    text = result if isinstance(result, str) else json.dumps(result)
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def process_paths(paths, outf):
    """Try to transcribe a list of image paths; write on success. Returns bool."""
    prompt = PROMPT_TEMPLATE.format(paths="\n".join(paths))
    for attempt in range(3):
        try:
            proc = run_claude(prompt)
            if proc.returncode != 0:
                stderr = proc.stderr.strip()[:200]
                stdout = proc.stdout.strip()[:200]
                print(f"    claude exit {proc.returncode} (attempt {attempt+1}) stderr={stderr!r} stdout={stdout!r}", flush=True)
                time.sleep(4 * (attempt + 1))
                continue
            arr = parse_result(proc.stdout)
            if not isinstance(arr, list):
                raise ValueError("expected JSON array, got " + type(arr).__name__)
            if len(arr) != len(paths):
                raise ValueError(f"expected {len(paths)} objects, got {len(arr)}")
            for obj in arr:
                outf.write(json.dumps(obj, ensure_ascii=False) + "\n")
            outf.flush()
            return True
        except Exception as e:
            print(f"    error attempt {attempt+1}: {e}", flush=True)
            time.sleep(4 * (attempt + 1))
    return False


def main():
    files = sorted(
        f for f in os.listdir(IMG)
        if f.lower().endswith(".png") and not f.startswith("Screenshot 2026-09-01")
    )
    done = load_done()
    todo = [f for f in files if f"images/{f}" not in done]
    print(f"total={len(files)} already_done={len(done)} todo={len(todo)}", flush=True)

    with open(OUT, "a", encoding="utf-8") as outf:
        i = 0
        while i < len(todo):
            batch = todo[i:i + BATCH_SIZE]
            batch_paths = [f"images/{f}" for f in batch]
            print(f"BATCH {i // BATCH_SIZE + 1}: {len(batch)} images -> {batch[0]} ...", flush=True)
            ok = process_paths(batch_paths, outf)
            if ok:
                print(f"  OK ({len(batch)} objects)", flush=True)
                i += len(batch)
            else:
                # fall back to one image at a time for this batch
                print(f"  batch failed; retrying each image individually", flush=True)
                for f in batch:
                    single = [f"images/{f}"]
                    ok1 = process_paths(single, outf)
                    print(f"    {'OK' if ok1 else 'FAILED'} {f}", flush=True)
                    time.sleep(1)
                i += len(batch)
            time.sleep(2)

    print("DONE. output:", OUT, flush=True)


if __name__ == "__main__":
    main()
