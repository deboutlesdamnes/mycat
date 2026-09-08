# -*- coding: utf-8 -*-
"""MCAT practice-test passage authoring framework (format A of the plan).

Implements the data model, validation rules, and question_schema.json compilation
described in plans/longform_question_framework.md.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional

# --------------------------------------------------------------------------- #
# Enums / constants
# --------------------------------------------------------------------------- #
SECTIONS = {
    # short names used by the existing pipeline (generate_longform.SECTION_MAP)
    "Biological & Biochemical Foundations",
    "Chemical & Physical Foundations",
    "Psychological, Social, & Biological Foundations",
    "Critical Analysis and Reasoning Skills",
    # long names used by the framework document
    "Chemical and Physical Foundations of Biological Systems (Chem/Phys)",
    "Biological and Biochemical Foundations of Living Systems (Bio/Biochem)",
    "Psychological, Social, and Biological Foundations of Behavior (Psych/Soc)",
    "Critical Analysis and Reasoning Skills (CARS)",
}

SCIENCE_SKILLS = {"skill1", "skill2", "skill3", "skill4"}
CARS_SKILLS = {"cars-foc", "cars-rwt", "cars-rbt"}
DIFFICULTIES = {"easy", "medium", "hard"}
FIGURE_TYPES = {"line", "bar", "scatter", "table", "spectrum", "nmr", "ir", "diagram", "molecule"}

SCIENCE_QUESTIONS = 5
CARS_QUESTIONS = (5, 6)  # real MCAT CARS: 9 passages totaling 53 questions
TARGET_WORDS = 500
PASSAGE_WORDS = (420, 650)  # "around 500 words" for both science and CARS passages


# --------------------------------------------------------------------------- #
# FigureSpec
# --------------------------------------------------------------------------- #
@dataclass
class FigureSpec:
    number: int
    type: str
    caption: str
    spec: dict = field(default_factory=dict)
    alt: str = ""

    def validate(self) -> List[str]:
        errors = []
        if self.type not in FIGURE_TYPES:
            errors.append(f"figure {self.number}: unknown type '{self.type}'")
        if not self.caption.strip():
            errors.append(f"figure {self.number}: missing caption")
        if not isinstance(self.spec, dict):
            errors.append(f"figure {self.number}: spec must be a dict")
        elif self.spec.get("type") not in FIGURE_TYPES:
            errors.append(f"figure {self.number}: spec.type missing or invalid")
        else:
            errors.extend(self._render_errors())
        return errors

    def _render_errors(self) -> List[str]:
        """A figure that figure_lib can't draw would ship as a blank box, so a
        spec that renders to nothing (or to a placeholder) is a validation error.
        Skipped entirely when figure_lib isn't importable."""
        try:
            import figure_lib  # noqa: F401
        except ImportError:
            return []
        html = (self.render() or "").strip()
        if not html:
            return [f"figure {self.number}: spec is not renderable by figure_lib"]
        if "(no data)" in html or "(empty table)" in html:
            return [f"figure {self.number}: spec renders empty (no usable data points)"]
        return []

    def render(self) -> Optional[str]:
        """Render to SVG/HTML via figure_lib; None on failure."""
        try:
            import figure_lib
        except ImportError:
            return None
        try:
            return figure_lib.render_figure(self.spec)
        except Exception:
            return None


# --------------------------------------------------------------------------- #
# QuestionSpec
# --------------------------------------------------------------------------- #
@dataclass
class QuestionSpec:
    skill: str
    subtype: str
    difficulty: str
    question: str
    options: List[str]
    correct: int
    explanation: str
    figure_refs: List[int] = field(default_factory=list)
    own_figure: Optional[FigureSpec] = None

    def validate(self, is_cars: bool) -> List[str]:
        errors = []
        valid_skills = CARS_SKILLS if is_cars else SCIENCE_SKILLS
        if self.skill not in valid_skills:
            errors.append(f"question '{self.question[:30]}…': skill '{self.skill}' invalid for {'CARS' if is_cars else 'science'}")
        if self.difficulty not in DIFFICULTIES:
            errors.append(f"question '{self.question[:30]}…': invalid difficulty")
        if not self.question.strip():
            errors.append("question: missing stem")
        if not isinstance(self.options, list) or len(self.options) != 4:
            errors.append(f"question '{self.question[:30]}…': must have exactly 4 options")
        elif any(not str(o).strip() for o in self.options):
            errors.append(f"question '{self.question[:30]}…': empty option")
        if not (0 <= int(self.correct) <= 3):
            errors.append(f"question '{self.question[:30]}…': correct index out of range")
        if not self.explanation.strip():
            errors.append(f"question '{self.question[:30]}…': missing explanation")
        return errors


# --------------------------------------------------------------------------- #
# PassageSpec
# --------------------------------------------------------------------------- #
@dataclass
class PassageSpec:
    id: str
    section: str
    subject: str
    topic: str
    knowledge_points: List[str]
    passage: str
    questions: List[QuestionSpec]
    figures: List[FigureSpec] = field(default_factory=list)
    attribution: str = ""
    is_cars: bool = False

    def validate(self) -> List[str]:
        errors = []
        if not self.id.strip():
            errors.append("missing id")
        if self.section not in SECTIONS:
            errors.append(f"unknown section '{self.section}'")
        if not self.subject.strip():
            errors.append("missing subject")
        if not self.topic.strip():
            errors.append("missing topic")
        if not self.knowledge_points:
            errors.append("missing knowledge_points")
        if not self.passage.strip():
            errors.append("missing passage text")

        wc = len(self.passage.split())
        lo, hi = PASSAGE_WORDS
        if not (lo <= wc <= hi):
            errors.append(f"passage word count {wc} outside [{lo}, {hi}] (target {TARGET_WORDS})")

        if self.is_cars and self.figures:
            errors.append("CARS passages must not have figures")
        elif not self.is_cars:
            errors.extend(self._figure_requirement_errors())

        if self.is_cars:
            lo_q, hi_q = CARS_QUESTIONS
            if not (lo_q <= len(self.questions) <= hi_q):
                errors.append(f"CARS passage must have {lo_q}-{hi_q} questions, got {len(self.questions)}")
        else:
            if len(self.questions) != SCIENCE_QUESTIONS:
                errors.append(f"must have exactly {SCIENCE_QUESTIONS} questions, got {len(self.questions)}")

        nums = [f.number for f in self.figures]
        if len(nums) != len(set(nums)):
            errors.append("figure numbers must be unique")

        for f in self.figures:
            errors.extend(f.validate())

        for q in self.questions:
            errors.extend(q.validate(self.is_cars))
            for ref in q.figure_refs:
                if ref not in nums:
                    errors.append(f"figure_ref {ref} does not exist")
            if q.own_figure is not None:
                errors.extend(q.own_figure.validate())

        # skill-mix sanity (non-blocking only when explicit; keep as warning-free)
        if self.is_cars:
            if any(q.skill not in CARS_SKILLS for q in self.questions):
                errors.append("CARS passage uses a science skill")
        else:
            if any(q.skill not in SCIENCE_SKILLS for q in self.questions):
                errors.append("science passage uses a CARS skill")

        return errors

    def _figure_requirement_errors(self) -> List[str]:
        """Science passages are built around data: the set must ship a figure,
        the passage prose must point the reader at it, and at least one question
        must actually use it. Without all three the passage reads as if an image
        were missing from the page."""
        if not self.figures:
            return ["science passage must include at least one figure "
                    "(with the passage text referring to it as 'Figure 1')"]
        errors = []
        cited = set(re.findall("(?:Figure|Table)[ ]*([0-9]+)", self.passage))
        for f in self.figures:
            # Accept either label: a table is often cited as "Figure 1" and vice versa.
            label = "Table" if f.type == "table" else "Figure"
            if str(f.number) not in cited:
                errors.append(
                    "passage text never refers to {0} {1}; cite it in the prose "
                    "(e.g. '... are shown in {0} {1}')".format(label, f.number)
                )
        if not any(q.figure_refs or q.own_figure for q in self.questions):
            errors.append("no question references a figure; at least one question "
                          "must set figure_refs to a figure number")
        return errors

    def _figure_for(self, refs: List[int]) -> Optional[FigureSpec]:
        for f in self.figures:
            if f.number in refs:
                return f
        return None

    def compile_to_schema(self) -> List[dict]:
        """Compile to one question_schema.json record per question."""
        records = []
        for i, q in enumerate(self.questions, 1):
            rec = {
                "id": f"{self.id}-q{i:02d}",
                "section": self.section,
                "subject": self.subject,
                "topic": self.topic,
                "knowledge_point": "; ".join(self.knowledge_points),
                "type": "passage",
                "skill": q.skill,
                "subtype": q.subtype,
                "difficulty": q.difficulty,
                "passage": self.passage,
                "question": q.question,
                "options": q.options,
                "correct": q.correct,
                "explanation": q.explanation,
            }
            # The figure belongs to the passage, not to one question, so every
            # record in the set carries it — the player shows it beside the
            # passage whichever question is on screen.
            fig = (q.own_figure
                   or self._figure_for(q.figure_refs)
                   or (self.figures[0] if self.figures else None))
            if fig is not None:
                rec["figure"] = fig.render() or ""
                rec["figure_type"] = fig.type
                rec["figure_caption"] = fig.caption
                rec["figure_alt"] = fig.alt
                # Keep the source spec so a figure can be redrawn later (a
                # figure_lib improvement, a restyle) without re-running the model.
                rec["figure_spec"] = fig.spec
            records.append(rec)
        return records

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "section": self.section,
            "subject": self.subject,
            "topic": self.topic,
            "knowledge_points": self.knowledge_points,
            "passage": self.passage,
            "is_cars": self.is_cars,
            "attribution": self.attribution,
            "figures": [
                {"number": f.number, "type": f.type, "caption": f.caption, "alt": f.alt, "spec": f.spec}
                for f in self.figures
            ],
            "questions": [
                {
                    "skill": q.skill,
                    "subtype": q.subtype,
                    "difficulty": q.difficulty,
                    "question": q.question,
                    "options": q.options,
                    "correct": q.correct,
                    "explanation": q.explanation,
                    "figure_refs": q.figure_refs,
                }
                for q in self.questions
            ],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PassageSpec":
        figures = [
            FigureSpec(
                number=int(f.get("number", i + 1)),
                type=f.get("type", "line"),
                caption=f.get("caption", ""),
                spec=f.get("spec", {}),
                alt=f.get("alt", ""),
            )
            for i, f in enumerate(d.get("figures") or [])
        ]
        questions = []
        for q in d.get("questions") or []:
            if not isinstance(q, dict):
                continue
            stem = q.get("question") or q.get("stem") or q.get("prompt") or ""
            opts = q.get("options")
            if not isinstance(opts, list):
                opts = []
            try:
                correct = int(q.get("correct", 0))
            except (TypeError, ValueError):
                correct = 0
            diff = str(q.get("difficulty", "medium")).strip().lower()
            if diff not in DIFFICULTIES:
                diff = "medium"
            questions.append(QuestionSpec(
                skill=q.get("skill", "skill2"),
                subtype=q.get("subtype", "application"),
                difficulty=diff,
                question=stem,
                options=opts,
                correct=correct,
                explanation=q.get("explanation", ""),
                figure_refs=[int(r) for r in q.get("figure_refs", [])],
            ))
        return cls(
            id=d.get("id", ""),
            section=d.get("section", ""),
            subject=d.get("subject", ""),
            topic=d.get("topic", ""),
            knowledge_points=d.get("knowledge_points", []),
            passage=d.get("passage", ""),
            questions=questions,
            figures=figures,
            attribution=d.get("attribution", ""),
            is_cars=bool(d.get("is_cars", False)),
        )


# --------------------------------------------------------------------------- #
# Writer prompt
# --------------------------------------------------------------------------- #
LONGFORM_PASSAGE_SYSTEM = """\
You are an expert MCAT question writer producing authentic practice-test PASSAGE sets.

Given a subject/topic and reference excerpts from a study corpus, write ONE passage set
that mirrors the real MCAT format:

- A passage header "Passage N (Questions X-Y)" is implied; do NOT include it in the text.
- Science passages have a context -> methods -> results arc: 4 substantial paragraphs,
  420-650 words total (aim for ~500; count the words before returning).
- CARS passages (is_cars=true) are humanities/social-science texts, 420-650 words
  (aim for ~500), NO figures.
- Science passages have exactly 5 questions; CARS passages have 5 or 6 questions.
- Each question has exactly 4 options and one correct answer (0-based index).
- difficulty must be exactly one of "easy", "medium", "hard" (lowercase).
- Questions use lead-ins such as "Which of the following...", "Based on Figure 1...",
  "According to the passage...", "Which conclusion is best supported by the data?".
- Skills: skill1 (knowledge), skill2 (reasoning), skill3 (research design),
  skill4 (data/statistical). CARS uses cars-foc, cars-rwt, cars-rbt.
- EVERY science passage MUST include exactly one figure - the reference image the
  passage is built around. It has: number (1), type, caption, alt, and a "spec"
  object that figure_lib.render_figure can draw. Requirements:
    * The passage prose MUST point the reader at it by name ("... are shown in
      Figure 1", "Table 1 summarizes ..."). A passage that never cites its figure
      is rejected.
    * At least one question MUST set "figure_refs": [1] and be answerable only by
      reading the figure.
    * The spec MUST carry real data - the numbers a test-taker reads off to answer.
      Use one of these shapes exactly:
      line/bar/scatter: {"type":"line","title":"...","xLabel":"...","yLabel":"...",
                         "series":[{"name":"...","points":[[x,y],[x,y],...]}]}
      table:            {"type":"table","columns":["...","..."],"rows":[["...","..."],...]}
      spectrum:         {"type":"spectrum","kind":"1h-nmr","title":"...",
                         "peaks":[{"shift":7.2,"height":0.8,"label":"..."}]}
      diagram:          {"type":"diagram","title":"...","nodes":[{"id":"a","label":"..."}],
                         "edges":[{"from":"a","to":"b","label":"..."}]}
    * Empty or placeholder specs (no points, no rows) are rejected.
- Every explanation teaches: state the principle, cite the passage/data, and debunk each distractor.
- Original content only; do not copy excerpts verbatim.

Return ONLY a JSON object with EXACTLY these keys and shapes:

{
  "id": "...",
  "section": "...",
  "subject": "...",
  "topic": "...",
  "knowledge_points": ["..."],
  "passage": "...",
  "is_cars": false,
  "attribution": "",
  "figures": [
    {"number": 1, "type": "line", "caption": "...", "alt": "...",
     "spec": {"type": "line", "title": "...", "xLabel": "...", "yLabel": "...",
              "series": [{"name": "...", "points": [[x, y], ...]}]}}
  ],
  "questions": [
    {"skill": "skill1", "subtype": "recall", "difficulty": "medium",
     "question": "...", "options": ["...", "...", "...", "..."],
     "correct": 0, "explanation": "...", "figure_refs": [1]}
  ]
}

The "questions" array must contain exactly 5 question objects for a science passage,
or 5-6 question objects for a CARS passage.

The "figures" array must contain exactly one figure for a science passage, and must
be empty ([]) for a CARS passage.

Every question object MUST include the exact keys: skill, subtype, difficulty,
question, options (4 strings), correct (int 0-3), explanation, figure_refs (list of
figure numbers, or [] when the question does not reference a figure).
"""


def build_passage_user(subject, topic, excerpts_text, n_questions=None, is_cars=False):
    ref = ""
    for i, ex in enumerate(excerpts_text, 1):
        ref += f"\n--- excerpt {i} ---\n{ex}\n"
    if not ref:
        ref = "(no corpus excerpt found)"
    count = f" Write exactly {n_questions} questions." if n_questions else f" Write exactly {SCIENCE_QUESTIONS} questions."
    if is_cars:
        fig = "This is a CARS passage: no figures (use an empty figures array)."
    else:
        fig = (
            "Include exactly one figure - the reference image for this passage. Cite it "
            "in the passage text as Figure 1 (or Table 1), and have at least one question "
            "reference it via figure_refs: [1]."
        )
    return (
        f"Subject: {subject}. Topic: {topic}.\n"
        f"Reference material from the study corpus (ground your passage in this):\n{ref}\n"
        f"Passage length: around {TARGET_WORDS} words.\n"
        f"{fig}\n"
        f"Generate one practice-test passage set.{count} Return JSON."
    )
