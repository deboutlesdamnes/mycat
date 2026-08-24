# -*- coding: utf-8 -*-
"""Full-length MCAT generation spec: topic -> number of questions per section.

Counts balance to a full exam:
  Bio/Biochem 59, Chem/Phys 59, Psych/Soc 59, CARS 53  (230 total).
"""

BIO_BIOCHEM = {
    "Biology": [
        ("The Cell", 4),
        ("Reproduction", 4),
        ("Embryogenesis and Development", 3),
        ("The Nervous System", 3),
        ("The Endocrine System", 3),
        ("The Respiratory System", 3),
        ("The Cardiovascular System", 3),
        ("The Immune System", 3),
        ("The Digestive System", 3),
        ("Homeostasis", 3),
        ("The Musculoskeletal System", 3),
        ("Genetics and Evolution", 3),
    ],
    "Biochemistry": [
        ("Amino Acids, Peptides, and Proteins", 3),
        ("Enzymes and Enzyme Kinetics", 2),
        ("Carbohydrates and Glycobiology", 2),
        ("Lipids and Biological Membranes", 2),
        ("DNA Structure and Replication", 2),
        ("Transcription and Translation", 2),
        ("Metabolism: Glycolysis, TCA Cycle, and Oxidative Phosphorylation", 2),
    ],
    "General Chemistry": [
        ("Acids and Bases", 1),
        ("Chemical Equilibrium", 1),
        ("Oxidation-Reduction Reactions", 1),
    ],
    "Organic Chemistry": [
        ("Functional Groups and Nomenclature", 1),
        ("Stereochemistry", 1),
        ("Carbonyl Chemistry", 1),
    ],
}

CHEM_PHYS = {
    "General Chemistry": [
        ("Atomic Structure", 2),
        ("The Periodic Table", 2),
        ("Bonding and Chemical Interactions", 2),
        ("Compounds and Stoichiometry", 2),
        ("Chemical Kinetics", 1),
        ("Equilibrium", 2),
        ("Thermochemistry", 2),
        ("The Gas Phase", 1),
        ("Solutions", 1),
        ("Acids and Bases", 1),
        ("Oxidation-Reduction Reactions", 1),
        ("Electrochemistry", 1),
    ],
    "Physics": [
        ("Kinematics and Dynamics", 3),
        ("Work and Energy", 2),
        ("Thermodynamics", 2),
        ("Fluids", 2),
        ("Electrostatics and Magnetism", 3),
        ("Circuits", 2),
        ("Waves and Sound", 2),
        ("Light and Optics", 2),
    ],
    "Organic Chemistry": [
        ("Nomenclature and Functional Groups", 2),
        ("Stereochemistry and Isomers", 2),
        ("Acids and Bases in Organic Chemistry", 1),
        ("Substitution and Elimination Reactions", 2),
        ("Carbonyl Chemistry", 2),
        ("Laboratory Techniques and Spectroscopy", 3),
    ],
    "Biochemistry": [
        ("Amino Acids and Proteins", 2),
        ("Enzymes", 2),
        ("Carbohydrates and Lipids", 2),
        ("Metabolism: Glycolysis, TCA Cycle, and Oxidative Phosphorylation", 3),
        ("Nucleic Acids and Gene Expression", 2),
    ],
}

PSYCH_SOC = {
    "Psychology": [
        ("Sensation and Perception", 3),
        ("Learning", 3),
        ("Memory", 3),
        ("Cognition and Language", 3),
        ("Consciousness and Sleep", 2),
        ("Motivation and Emotion", 3),
        ("Stress and Coping", 2),
        ("Personality", 3),
        ("Psychological Disorders", 3),
        ("Developmental Psychology", 3),
        ("Social Psychology", 4),
        ("Biological Bases of Behavior", 3),
        ("Research Methods and Statistics", 3),
    ],
    "Sociology": [
        ("Social Structure and Institutions", 3),
        ("Culture and Socialization", 3),
        ("Social Stratification and Inequality", 3),
        ("Demography and Urbanization", 3),
        ("Social Interaction and Groups", 3),
        ("Social Change and Globalization", 3),
    ],
    "Biology": [
        ("Nervous and Endocrine Systems", 3),
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

SECTIONS = [
    ("Biological & Biochemical Foundations", BIO_BIOCHEM),
    ("Chemical & Physical Foundations", CHEM_PHYS),
    ("Psychological, Social, & Biological Foundations", PSYCH_SOC),
]


def build_tasks():
    tasks = []
    for section, subjects in SECTIONS:
        for subject, topics in subjects.items():
            for topic, n in topics:
                tasks.append({
                    "section": section,
                    "subject": subject,
                    "topic": topic,
                    "n": n,
                    "cars": False,
                })
    for topic, n in CARS_PASSAGES:
        tasks.append({
            "section": "Critical Analysis and Reasoning Skills",
            "subject": "Critical Analysis and Reasoning Skills (CARS)",
            "topic": topic,
            "n": n,
            "cars": True,
        })
    return tasks


def total_questions():
    return sum(t["n"] for t in build_tasks())
