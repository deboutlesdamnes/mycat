# -*- coding: utf-8 -*-
"""Data models: Passage, Question, Section."""
from collections import OrderedDict


class Passage:
    def __init__(self, num, q0, q1):
        self.num = num
        self.q0 = q0
        self.q1 = q1
        self.lines = []
        self.src = []
        self.figures = OrderedDict()  # num -> {"caption", "description", "src": []}
        self.tables = OrderedDict()   # num -> {"caption", "rows"/"markdown", "src": []}
        self.questions = OrderedDict()

    def add_figure(self, num, caption, description="", src=None):
        src = src or ""
        if num in self.figures:
            f = self.figures[num]
            if len(description or "") > len(f.get("description") or ""):
                f["description"] = description
            if len(caption or "") > len(f.get("caption") or ""):
                f["caption"] = caption
            if src and src not in f.get("src", []):
                f.setdefault("src", []).append(src)
        else:
            self.figures[num] = {"caption": caption, "description": description, "src": [src] if src else []}

    def add_table(self, num, caption, rows=None, markdown=None, src=None):
        src = src or ""
        rows = rows if rows is not None else []
        if num in self.tables:
            t = self.tables[num]
            if rows and (not t.get("rows") or len(rows) > len(t.get("rows") or [])):
                t["rows"] = rows
            if markdown:
                t["markdown"] = markdown
            if len(caption or "") > len(t.get("caption") or ""):
                t["caption"] = caption
            if src and src not in t.get("src", []):
                t.setdefault("src", []).append(src)
        else:
            self.tables[num] = {"caption": caption, "rows": rows, "src": [src] if src else []}
            if markdown:
                self.tables[num]["markdown"] = markdown

    def merge(self, other):
        if len(other.lines) > len(self.lines):
            self.lines = other.lines
        for k, v in other.figures.items():
            if k not in self.figures:
                self.figures[k] = v
            else:
                if len(v.get("description") or "") > len(self.figures[k].get("description") or ""):
                    self.figures[k]["description"] = v["description"]
                if len(v.get("caption") or "") > len(self.figures[k].get("caption") or ""):
                    self.figures[k]["caption"] = v["caption"]
                self.figures[k]["src"] = sorted(set(self.figures[k].get("src", [])) | set(v.get("src", [])))
        for k, v in other.tables.items():
            if k not in self.tables:
                self.tables[k] = v
            elif len(v.get("rows") or []) > len(self.tables[k].get("rows") or []):
                self.tables[k] = v
        for k, v in other.questions.items():
            if k in self.questions:
                self.questions[k].merge(v)
            else:
                self.questions[k] = v


class Question:
    def __init__(self, num):
        self.num = num
        self.lines = []
        self.src = []
        self.figures = OrderedDict()

    def add_figure(self, num, caption, description="", src=None):
        src = src or ""
        if num in self.figures:
            f = self.figures[num]
            if len(description or "") > len(f.get("description") or ""):
                f["description"] = description
            if len(caption or "") > len(f.get("caption") or ""):
                f["caption"] = caption
            if src and src not in f.get("src", []):
                f.setdefault("src", []).append(src)
        else:
            self.figures[num] = {"caption": caption, "description": description, "src": [src] if src else []}

    def merge(self, other):
        if len(other.lines) > len(self.lines):
            self.lines = other.lines
        self.src = sorted(set(self.src) | set(other.src))
        for k, v in other.figures.items():
            if k not in self.figures:
                self.figures[k] = v


class Section:
    def __init__(self, passages=None, standalone=None):
        self.passages = passages if passages is not None else OrderedDict()
        self.standalone = standalone if standalone is not None else OrderedDict()

    def passage_questions(self):
        return sum(len(p.questions) for p in self.passages.values())

    def total_questions(self):
        return self.passage_questions() + len(self.standalone)
