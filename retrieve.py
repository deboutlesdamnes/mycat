# -*- coding: utf-8 -*-
"""Retrieve relevant corpus excerpts for a topic (lightweight keyword/chunk search).

The full corpus text lives in extracted/*.txt (all 8 files). We chunk each file
and score chunks by keyword overlap with the topic, returning the top excerpts.
"""
import os
import re

EXTRACTED = r"c:\Users\jason\Documents\mycat\extracted"
_CHUNK_SIZE = 1200
_CHUNK_OVERLAP = 200
_cache = None  # list of (filename, chunk_text)


def _files():
    out = {}
    for fn in sorted(os.listdir(EXTRACTED)):
        if fn.lower().endswith(".txt"):
            with open(os.path.join(EXTRACTED, fn), encoding="utf-8") as f:
                out[fn] = f.read()
    return out


def _chunks(text):
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + _CHUNK_SIZE, n)
        chunks.append(text[start:end])
        if end >= n:
            break
        start = end - _CHUNK_OVERLAP
    return chunks


def _get_cache():
    global _cache
    if _cache is None:
        items = []
        for fn, text in _files().items():
            for ch in _chunks(text):
                items.append((fn, ch))
        _cache = items
    return _cache


def _keywords(topic):
    stop = {"the", "and", "of", "for", "with", "in", "on", "a", "an", "to", "or", "vs"}
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", topic.lower())
    return [w for w in words if w not in stop]


def retrieve(topic, restrict=None, k=3, max_chars=1500):
    """Return up to k relevant corpus excerpts for a topic."""
    kw = _keywords(topic)
    phrase = topic.lower()
    noise = ("table of contents", "title page", "===file titlepage", "cover", "copyright")
    scored = []
    for fn, ch in _get_cache():
        if restrict and fn not in restrict:
            continue
        low = ch.lower()
        head = low[:300]
        if any(n in head for n in noise):
            continue
        score = sum(low.count(w) for w in kw)
        if phrase in low:
            score += 8
        if score > 0:
            scored.append((score, fn, ch))
    scored.sort(key=lambda x: -x[0])
    out = []
    seen = set()
    for score, fn, ch in scored:
        sig = ch[:100].lower()
        if sig in seen:
            continue
        seen.add(sig)
        out.append({"file": fn, "score": score, "text": ch.strip()[:max_chars]})
        if len(out) >= k:
            break
    return out
