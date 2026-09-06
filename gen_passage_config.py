# -*- coding: utf-8 -*-
"""Full-length passage-majority plan.

The real MCAT split is ~75% passage-based / ~25% discrete in science sections and
100% passage-based in CARS. This module encodes that as:

  science sections: 44 passage questions + 15 discrete = 59
  CARS:             53 passage questions +  0 discrete = 53
  total:            230 questions (185 passage + 45 discrete)
"""
BIO = "Biological & Biochemical Foundations"
CHEM = "Chemical & Physical Foundations"
PSYCH = "Psychological, Social, & Biological Foundations"
CARS = "Critical Analysis and Reasoning Skills"
CARS_SUBJECT = "Critical Analysis and Reasoning Skills (CARS)"

# section -> list of (subject, topic, n_questions) for PASSAGE sets (4-7 each)
SCIENCE_PASSAGES = {
    CHEM: [
        ("Physics", "Kinematics and Dynamics", 4),
        ("Physics", "Fluids", 4),
        ("Physics", "Electrostatics and Magnetism", 5),
        ("Physics", "Circuits", 4),
        ("General Chemistry", "Thermochemistry", 4),
        ("General Chemistry", "Equilibrium", 4),
        ("Organic Chemistry", "Carbonyl Chemistry", 4),
        ("Organic Chemistry", "Laboratory Techniques and Spectroscopy", 5),
        ("Biochemistry", "Enzymes", 5),
        ("Biochemistry", "Metabolism: Glycolysis, TCA Cycle, and Oxidative Phosphorylation", 5),
    ],
    BIO: [
        ("Biology", "The Cell", 5),
        ("Biology", "The Nervous System", 4),
        ("Biology", "The Cardiovascular System", 4),
        ("Biology", "The Immune System", 4),
        ("Biology", "Genetics and Evolution", 5),
        ("Biochemistry", "Enzymes and Enzyme Kinetics", 4),
        ("Biochemistry", "DNA Structure and Replication", 4),
        ("Biochemistry", "Transcription and Translation", 4),
        ("Biochemistry", "Metabolism: Glycolysis, TCA Cycle, and Oxidative Phosphorylation", 5),
        ("Biology", "The Endocrine System", 5),
    ],
    PSYCH: [
        ("Psychology", "Memory", 5),
        ("Psychology", "Learning", 4),
        ("Psychology", "Social Psychology", 5),
        ("Psychology", "Psychological Disorders", 4),
        ("Psychology", "Developmental Psychology", 4),
        ("Psychology", "Motivation and Emotion", 4),
        ("Sociology", "Social Stratification and Inequality", 4),
        ("Sociology", "Culture and Socialization", 4),
        ("Psychology", "Sensation and Perception", 5),
        ("Sociology", "Social Interaction and Groups", 5),
    ],
}

# section -> list of (subject, topic, n) for DISCRETE questions (the minority)
SCIENCE_DISCRETE = {
    CHEM: [
        ("General Chemistry", "Atomic Structure", 1),
        ("General Chemistry", "The Periodic Table", 1),
        ("General Chemistry", "Bonding and Chemical Interactions", 1),
        ("General Chemistry", "Compounds and Stoichiometry", 1),
        ("General Chemistry", "Chemical Kinetics", 1),
        ("General Chemistry", "The Gas Phase", 1),
        ("General Chemistry", "Solutions", 1),
        ("General Chemistry", "Acids and Bases", 1),
        ("General Chemistry", "Oxidation-Reduction Reactions", 1),
        ("General Chemistry", "Electrochemistry", 1),
        ("Physics", "Thermodynamics", 1),
        ("Physics", "Waves and Sound", 1),
        ("Physics", "Light and Optics", 1),
        ("Organic Chemistry", "Nomenclature and Functional Groups", 1),
        ("Organic Chemistry", "Stereochemistry and Isomers", 1),
    ],
    BIO: [
        ("Biology", "Reproduction", 1),
        ("Biology", "Embryogenesis and Development", 1),
        ("Biology", "The Respiratory System", 1),
        ("Biology", "The Digestive System", 1),
        ("Biology", "Homeostasis", 1),
        ("Biology", "The Musculoskeletal System", 1),
        ("Biochemistry", "Amino Acids, Peptides, and Proteins", 1),
        ("Biochemistry", "Carbohydrates and Glycobiology", 1),
        ("Biochemistry", "Lipids and Biological Membranes", 1),
        ("General Chemistry", "Acids and Bases", 1),
        ("General Chemistry", "Chemical Equilibrium", 1),
        ("General Chemistry", "Oxidation-Reduction Reactions", 1),
        ("Organic Chemistry", "Functional Groups and Nomenclature", 1),
        ("Organic Chemistry", "Stereochemistry", 1),
        ("Organic Chemistry", "Carbonyl Chemistry", 1),
    ],
    PSYCH: [
        ("Psychology", "Cognition and Language", 2),
        ("Psychology", "Consciousness and Sleep", 1),
        ("Psychology", "Stress and Coping", 1),
        ("Psychology", "Personality", 2),
        ("Psychology", "Biological Bases of Behavior", 2),
        ("Psychology", "Research Methods and Statistics", 2),
        ("Sociology", "Social Structure and Institutions", 2),
        ("Sociology", "Demography and Urbanization", 1),
        ("Sociology", "Social Change and Globalization", 1),
        ("Biology", "Nervous and Endocrine Systems", 1),
    ],
}

CARS_PASSAGES = [
    ("Philosophy and Ethics", 6),
    ("Literature and Literary Criticism", 5),
    ("Art History and Aesthetics", 5),
    ("History", 6),
    ("Political Science and Government", 5),
    ("Economics and Business", 5),
    ("Sociology and Anthropology", 6),
    ("Psychology and Social Behavior", 5),
    ("Philosophy of Science and Technology", 5),
    ("Cultural Studies and Religion", 5),
]


def build_passage_plan():
    """Return {"passages": [...], "discrete": [...]} with normalized task dicts."""
    passages, discrete = [], []
    for section, items in SCIENCE_PASSAGES.items():
        for subject, topic, n in items:
            passages.append({"section": section, "subject": subject, "topic": topic,
                             "n": n, "cars": False, "is_cars": False})
    for section, items in SCIENCE_DISCRETE.items():
        for subject, topic, n in items:
            discrete.append({"section": section, "subject": subject, "topic": topic,
                             "n": n, "cars": False, "is_cars": False})
    for topic, n in CARS_PASSAGES:
        passages.append({"section": CARS, "subject": CARS_SUBJECT, "topic": topic,
                         "n": n, "cars": True, "is_cars": True})
    return {"passages": passages, "discrete": discrete}


def validate_plan():
    """Return a list of human-readable errors; empty means the plan is sound."""
    errors = []
    plan = build_passage_plan()

    for p in plan["passages"]:
        if not (4 <= p["n"] <= 7):
            errors.append(f"passage '{p['topic']}' has {p['n']} questions (must be 4-7)")

    def section_totals(items):
        tot = {}
        for it in items:
            tot[it["section"]] = tot.get(it["section"], 0) + it["n"]
        return tot

    psec = section_totals(plan["passages"])
    dsec = section_totals(plan["discrete"])

    expected = {
        CHEM: (44, 15), BIO: (44, 15), PSYCH: (44, 15), CARS: (53, 0),
    }
    for sec, (p_exp, d_exp) in expected.items():
        if psec.get(sec, 0) != p_exp:
            errors.append(f"{sec}: passage questions {psec.get(sec, 0)} != {p_exp}")
        if dsec.get(sec, 0) != d_exp:
            errors.append(f"{sec}: discrete questions {dsec.get(sec, 0)} != {d_exp}")

    total_p = sum(psec.values())
    total_d = sum(dsec.values())
    if total_p + total_d != 230:
        errors.append(f"total {total_p + total_d} != 230")
    if not (total_p > total_d):
        errors.append(f"passages must be the majority: {total_p} <= {total_d}")
    return errors


def passage_question_count():
    return sum(p["n"] for p in build_passage_plan()["passages"])


def discrete_question_count():
    return sum(d["n"] for d in build_passage_plan()["discrete"])
