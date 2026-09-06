# -*- coding: utf-8 -*-
"""Full-length exam plan matching the real MCAT section sizes, with a 50/50
passage-vs-discrete split in science sections and 100% passage-based CARS.

Every science passage set is exactly 5 questions; CARS passages are 5-6 questions
(9 CARS passages totaling 53, as on the real exam). This module encodes:

  science sections: 30 passage questions + 29 discrete = 59
  CARS:             53 passage questions +  0 discrete = 53
  total:            230 questions (143 passage + 87 discrete)
"""
BIO = "Biological & Biochemical Foundations"
CHEM = "Chemical & Physical Foundations"
PSYCH = "Psychological, Social, & Biological Foundations"
CARS = "Critical Analysis and Reasoning Skills"
CARS_SUBJECT = "Critical Analysis and Reasoning Skills (CARS)"

# section -> list of (subject, topic, n_questions) for science PASSAGE sets (5 each)
SCIENCE_PASSAGES = {
    CHEM: [
        ("Physics", "Kinematics and Dynamics", 5),
        ("Physics", "Electrostatics and Magnetism", 5),
        ("General Chemistry", "Equilibrium", 5),
        ("Organic Chemistry", "Carbonyl Chemistry", 5),
        ("Biochemistry", "Enzymes", 5),
        ("Biochemistry", "Metabolism: Glycolysis, TCA Cycle, and Oxidative Phosphorylation", 5),
    ],
    BIO: [
        ("Biology", "The Cell", 5),
        ("Biology", "The Nervous System", 5),
        ("Biology", "Genetics and Evolution", 5),
        ("Biochemistry", "Enzymes and Enzyme Kinetics", 5),
        ("Biochemistry", "DNA Structure and Replication", 5),
        ("Biology", "The Endocrine System", 5),
    ],
    PSYCH: [
        ("Psychology", "Memory", 5),
        ("Psychology", "Learning", 5),
        ("Psychology", "Social Psychology", 5),
        ("Psychology", "Psychological Disorders", 5),
        ("Sociology", "Social Stratification and Inequality", 5),
        ("Psychology", "Sensation and Perception", 5),
    ],
}

# section -> list of (subject, topic, n) for DISCRETE (stand-alone) questions.
# Science sections are 50/50: 29 discrete questions each.
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
        ("General Chemistry", "Thermochemistry", 1),
        ("General Chemistry", "Chemical Equilibrium", 1),
        ("Physics", "Thermodynamics", 1),
        ("Physics", "Waves and Sound", 1),
        ("Physics", "Light and Optics", 1),
        ("Physics", "Fluids", 1),
        ("Physics", "Circuits", 1),
        ("Physics", "Electrostatics and Magnetism", 1),
        ("Physics", "Kinematics and Dynamics", 1),
        ("Physics", "Work and Energy", 1),
        ("Organic Chemistry", "Nomenclature and Functional Groups", 1),
        ("Organic Chemistry", "Stereochemistry and Isomers", 1),
        ("Organic Chemistry", "Substitution and Elimination Reactions", 1),
        ("Organic Chemistry", "Carbonyl Chemistry", 1),
        ("Organic Chemistry", "Acids and Bases in Organic Chemistry", 1),
        ("Organic Chemistry", "Laboratory Techniques and Spectroscopy", 1),
        ("Biochemistry", "Amino Acids, Peptides, and Proteins", 1),
        ("Biochemistry", "Enzymes and Enzyme Kinetics", 1),
        ("Biochemistry", "Carbohydrates and Glycobiology", 1),
    ],
    BIO: [
        ("Biology", "Reproduction", 1),
        ("Biology", "Embryogenesis and Development", 1),
        ("Biology", "The Respiratory System", 1),
        ("Biology", "The Digestive System", 1),
        ("Biology", "Homeostasis", 1),
        ("Biology", "The Musculoskeletal System", 1),
        ("Biology", "The Cardiovascular System", 1),
        ("Biology", "The Immune System", 1),
        ("Biology", "Genetics and Evolution", 1),
        ("Biology", "The Endocrine System", 1),
        ("Biology", "The Nervous System", 1),
        ("Biology", "The Cell", 1),
        ("Biochemistry", "Amino Acids, Peptides, and Proteins", 1),
        ("Biochemistry", "Carbohydrates and Glycobiology", 1),
        ("Biochemistry", "Lipids and Biological Membranes", 1),
        ("Biochemistry", "DNA Structure and Replication", 1),
        ("Biochemistry", "Transcription and Translation", 1),
        ("Biochemistry", "Enzymes and Enzyme Kinetics", 1),
        ("Biochemistry", "Metabolism: Glycolysis, TCA Cycle, and Oxidative Phosphorylation", 1),
        ("Biochemistry", "Nucleic Acids and Gene Expression", 1),
        ("General Chemistry", "Acids and Bases", 1),
        ("General Chemistry", "Chemical Equilibrium", 1),
        ("General Chemistry", "Oxidation-Reduction Reactions", 1),
        ("General Chemistry", "Solutions", 1),
        ("General Chemistry", "Bonding and Chemical Interactions", 1),
        ("Organic Chemistry", "Functional Groups and Nomenclature", 1),
        ("Organic Chemistry", "Stereochemistry", 1),
        ("Organic Chemistry", "Carbonyl Chemistry", 1),
        ("Organic Chemistry", "Substitution and Elimination Reactions", 1),
    ],
    PSYCH: [
        ("Psychology", "Sensation and Perception", 1),
        ("Psychology", "Consciousness and Sleep", 1),
        ("Psychology", "Biological Bases of Behavior", 1),
        ("Psychology", "Memory", 1),
        ("Psychology", "Learning", 1),
        ("Psychology", "Cognition and Language", 1),
        ("Psychology", "Research Methods and Statistics", 1),
        ("Psychology", "Motivation and Emotion", 1),
        ("Psychology", "Personality", 1),
        ("Psychology", "Psychological Disorders", 1),
        ("Psychology", "Developmental Psychology", 1),
        ("Psychology", "Stress and Coping", 1),
        ("Psychology", "Self and Identity", 1),
        ("Psychology", "Biopsychosocial Model", 1),
        ("Psychology", "Social Psychology", 1),
        ("Psychology", "Attribution Theory", 1),
        ("Psychology", "Social Interaction and Groups", 1),
        ("Psychology", "Emotion", 1),
        ("Psychology", "Language and Cognition", 1),
        ("Sociology", "Culture and Socialization", 1),
        ("Sociology", "Sociology and Anthropology", 1),
        ("Sociology", "Social Structure and Institutions", 1),
        ("Sociology", "Social Stratification and Inequality", 1),
        ("Sociology", "Social Stratification", 1),
        ("Sociology", "Demography and Urbanization", 1),
        ("Sociology", "Social Change and Globalization", 1),
        ("Sociology", "Race and Ethnicity", 1),
        ("Sociology", "Health and Medicine", 1),
        ("Biology", "Nervous and Endocrine Systems", 1),
    ],
}

# CARS is 100% passage-based: 9 passages totaling 53 questions (mix of 5 and 6).
CARS_PASSAGES = [
    ("Philosophy and Ethics", 6),
    ("Literature and Literary Criticism", 5),
    ("Art History and Aesthetics", 6),
    ("History", 6),
    ("Political Science and Government", 6),
    ("Economics and Business", 6),
    ("Sociology and Anthropology", 6),
    ("Psychology and Social Behavior", 6),
    ("Philosophy of Science and Technology", 6),
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
        if p["is_cars"]:
            if p["n"] not in (5, 6):
                errors.append(f"CARS passage '{p['topic']}' has {p['n']} questions (must be 5-6)")
        else:
            if p["n"] != 5:
                errors.append(f"passage '{p['topic']}' has {p['n']} questions (must be exactly 5)")

    def section_totals(items):
        tot = {}
        for it in items:
            tot[it["section"]] = tot.get(it["section"], 0) + it["n"]
        return tot

    psec = section_totals(plan["passages"])
    dsec = section_totals(plan["discrete"])

    expected = {
        CHEM: (30, 29), BIO: (30, 29), PSYCH: (30, 29), CARS: (53, 0),
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
