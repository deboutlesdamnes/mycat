# -*- coding: utf-8 -*-
import unittest

from mcat_extract.longform import (
    FigureSpec,
    QuestionSpec,
    PassageSpec,
    build_passage_user,
)


def line_spec():
    return {
        "type": "line",
        "title": "t",
        "xLabel": "x",
        "yLabel": "y",
        "series": [{"name": "a", "points": [[0, 1], [1, 2]]}],
    }


def good_question():
    return QuestionSpec(
        skill="skill2",
        subtype="data-interp",
        difficulty="medium",
        question="Based on Figure 1, which is correct?",
        options=["A", "B", "C", "D"],
        correct=1,
        explanation="The correct one is B because ...",
        figure_refs=[1],
    )


def good_cars_question():
    return QuestionSpec(
        skill="cars-foc",
        subtype="main-idea",
        difficulty="medium",
        question="Which best expresses the central thesis?",
        options=["A", "B", "C", "D"],
        correct=0,
        explanation="The thesis is A because ...",
    )


def good_passage(is_cars=False):
    p = PassageSpec(
        id="p-test",
        section=("Critical Analysis and Reasoning Skills (CARS)" if is_cars
                 else "Biological & Biochemical Foundations"),
        subject=("Critical Analysis and Reasoning Skills (CARS)" if is_cars else "Biochemistry"),
        topic="Enzymes and Enzyme Kinetics",
        knowledge_points=["2.2 Reaction Rates"],
        passage=" ".join(["word"] * 497) + " see Figure 1 below",
        questions=[good_question() for _ in range(5)],
        figures=[] if is_cars else [FigureSpec(1, "line", "Fig 1", line_spec())],
        is_cars=is_cars,
    )
    return p


class TestFigureSpec(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(FigureSpec(1, "line", "cap", line_spec()).validate(), [])

    def test_invalid_type(self):
        errs = FigureSpec(1, "pie", "cap", {"type": "pie"}).validate()
        self.assertTrue(any("unknown type" in e for e in errs))

    def test_render_line(self):
        svg = FigureSpec(1, "line", "cap", line_spec()).render()
        self.assertIsNotNone(svg)
        self.assertTrue(svg.startswith("<svg"))

    def test_render_invalid_returns_none(self):
        self.assertIsNone(FigureSpec(1, "line", "cap", {}).render())


class TestQuestionSpec(unittest.TestCase):
    def test_valid_science(self):
        self.assertEqual(good_question().validate(is_cars=False), [])

    def test_wrong_option_count(self):
        q = good_question()
        q.options = ["A", "B", "C"]
        self.assertTrue(any("exactly 4 options" in e for e in q.validate(False)))

    def test_cars_skill_rejected_in_science(self):
        q = good_question()
        q.skill = "cars-foc"
        self.assertTrue(any("invalid for science" in e for e in q.validate(False)))

    def test_science_skill_rejected_in_cars(self):
        q = good_question()
        self.assertTrue(any("invalid for CARS" in e for e in q.validate(True)))


class TestPassageSpec(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(good_passage().validate(), [])

    def test_too_few_questions(self):
        p = good_passage()
        p.questions = p.questions[:4]
        self.assertTrue(any("must have exactly 5" in e for e in p.validate()))

    def test_science_six_questions_rejected(self):
        p = good_passage()
        p.questions = [good_question() for _ in range(6)]
        self.assertTrue(any("must have exactly 5" in e for e in p.validate()))

    def test_cars_five_or_six_questions_valid(self):
        for n in (5, 6):
            p = PassageSpec(
                id="p-cars",
                section="Critical Analysis and Reasoning Skills (CARS)",
                subject="Critical Analysis and Reasoning Skills (CARS)",
                topic="Philosophy and Ethics",
                knowledge_points=["Philosophy of Science and Technology"],
                passage=" ".join(["word"] * 500),
                questions=[good_cars_question() for _ in range(n)],
                figures=[],
                is_cars=True,
            )
            self.assertEqual(p.validate(), [], f"CARS {n}-question passage should be valid")

    def test_cars_with_figures_rejected(self):
        p = good_passage(is_cars=True)
        p.figures = [FigureSpec(1, "line", "cap", line_spec())]
        self.assertTrue(any("CARS passages must not have figures" in e for e in p.validate()))

    def test_science_passage_without_figure_rejected(self):
        p = good_passage()
        p.figures = []
        self.assertTrue(any("must include at least one figure" in e for e in p.validate()))

    def test_uncited_figure_rejected(self):
        p = good_passage()
        p.passage = " ".join(["word"] * 500)
        self.assertTrue(any("never refers to Figure 1" in e for e in p.validate()))

    def test_figure_cited_as_table_accepted(self):
        p = good_passage()
        p.figures = [FigureSpec(1, "table", "Table 1", {
            "type": "table", "columns": ["c1", "c2"], "rows": [["1", "2"]]})]
        p.passage = " ".join(["word"] * 497) + " see Table 1 below"
        self.assertEqual(p.validate(), [])

    def test_figure_never_referenced_by_a_question_rejected(self):
        p = good_passage()
        for q in p.questions:
            q.figure_refs = []
        self.assertTrue(any("no question references a figure" in e for e in p.validate()))

    def test_unrenderable_figure_spec_rejected(self):
        p = good_passage()
        p.figures = [FigureSpec(1, "line", "Fig 1", {"type": "line", "series": []})]
        self.assertTrue(any("draws nothing" in e for e in p.validate()))

    def test_figure_travels_with_every_question_in_the_set(self):
        p = good_passage()
        p.questions[0].figure_refs = []  # question that doesn't cite the figure
        records = p.compile_to_schema()
        self.assertTrue(all(r["figure"].startswith("<svg") for r in records))
        self.assertTrue(all(r["figure_caption"] == "Fig 1" for r in records))

    def test_bad_figure_ref(self):
        p = good_passage()
        p.questions[0].figure_refs = [99]
        self.assertTrue(any("figure_ref 99 does not exist" in e for e in p.validate()))

    def test_word_count_bounds(self):
        p = good_passage()
        p.passage = "short"
        self.assertTrue(any("word count" in e for e in p.validate()))

    def test_compile_to_schema(self):
        p = good_passage()
        records = p.compile_to_schema()
        self.assertEqual(len(records), 5)
        rec = records[0]
        self.assertEqual(rec["type"], "passage")
        self.assertEqual(rec["correct"], 1)
        self.assertEqual(rec["knowledge_point"], "2.2 Reaction Rates")
        self.assertEqual(rec["figure_type"], "line")
        self.assertTrue(rec["figure"].startswith("<svg"))
        self.assertEqual(rec["figure_spec"], line_spec())

    def test_round_trip_from_dict(self):
        p = good_passage()
        p2 = PassageSpec.from_dict(p.to_dict())
        self.assertEqual(p2.id, p.id)
        self.assertEqual(len(p2.questions), 5)
        self.assertEqual(p2.validate(), [])

    def test_build_user(self):
        user = build_passage_user("Biology", "The Cell", ["excerpt one", "excerpt two"])
        self.assertIn("Biology", user)
        self.assertIn("excerpt one", user)
        self.assertIn("excerpt two", user)
        self.assertIn("around 500 words", user)
        self.assertIn("exactly 5 questions", user)
        self.assertIn("Figure 1", user)

    def test_build_user_cars_asks_for_no_figures(self):
        user = build_passage_user("CARS", "Ethics", ["excerpt"], n_questions=6, is_cars=True)
        self.assertIn("no figures", user)


if __name__ == "__main__":
    unittest.main()
