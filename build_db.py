# -*- coding: utf-8 -*-
"""Build a SQLite database summarizing question types and knowledge points
from the MyCat corpus folder (MCAT study materials)."""
import sqlite3, os

DB = r"c:\Users\jason\Documents\mycat\mycat_knowledge.db"
if os.path.exists(DB):
    os.remove(DB)

conn = sqlite3.connect(DB)
c = conn.cursor()

c.executescript("""
CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);
CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT UNIQUE NOT NULL,
    title TEXT,
    publisher TEXT,
    format TEXT,
    subject TEXT
);
CREATE TABLE mcat_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    total_questions INTEGER,
    passages INTEGER,
    passage_based INTEGER,
    discrete INTEGER,
    content_breakdown TEXT
);
CREATE TABLE question_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    frequency TEXT,
    source TEXT
);
CREATE TABLE knowledge_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    chapter TEXT,
    section_number TEXT,
    topic TEXT NOT NULL,
    source TEXT
);
""")

SUBJECTS = [
    "Biology", "General Chemistry", "Organic Chemistry", "Biochemistry",
    "Physics", "Mathematics", "Critical Analysis and Reasoning Skills (CARS)",
    "Psychology", "Sociology",
]
for s in SUBJECTS:
    c.execute("INSERT INTO subjects(name) VALUES (?)", (s,))

SOURCES = [
    ("bio2021-2022.pdf", "Kaplan MCAT Biology Review 2021-2022", "Kaplan", "PDF", "Biology"),
    ("chembio.pdf", "MCAT Chemical and Physical Foundations of Biological Systems 2015", "McGraw-Hill Education", "PDF", "Chemistry & Physics"),
    ("critical_reasoning.epub", "Kaplan MCAT Critical Analysis and Reasoning Skills Review", "Kaplan", "EPUB", "Critical Analysis and Reasoning Skills (CARS)"),
    ("genchem.pdf", "General Chemistry Part I (Sections I-V)", "The Berkeley Review", "PDF", "General Chemistry"),
    ("genchem2019-2020.pdf", "Kaplan MCAT General Chemistry Review 2019-2020", "Kaplan", "PDF", "General Chemistry"),
    ("kphys_and_math.epub", "Kaplan MCAT Physics and Math Review", "Kaplan", "EPUB", "Physics & Mathematics"),
    ("p_physics_and_math.epub", "MCAT Physics and Math Review (New for MCAT 2015)", "The Princeton Review", "EPUB", "Physics & Mathematics"),
    ("qbook_2000.pdf", "MCAT QBook: Over 2,000 Questions Covering Every MCAT Science Topic", "Next Step Pre-Med", "PDF", "All science topics (question bank)"),
]
for s in SOURCES:
    c.execute("INSERT INTO sources(filename,title,publisher,format,subject) VALUES (?,?,?,?,?)", s)

MCAT_SECTIONS = [
    ("Chemical and Physical Foundations of Biological Systems (Chem/Phys)", 59, 10, 44, 15,
     "Biochemistry 25%, Biology 5%, General Chemistry 30%, Organic Chemistry 15%, Physics 25%"),
    ("Critical Analysis and Reasoning Skills (CARS)", 53, 9, 53, 0,
     "Humanities 50%, Social Sciences 50%"),
    ("Biological and Biochemical Foundations of Living Systems (Bio/Biochem)", 59, 10, 44, 15,
     "Biology 65%, Biochemistry 25%, General Chemistry 5%, Organic Chemistry 5%"),
    ("Psychological, Social, and Biological Foundations of Behavior (Psych/Soc)", 59, 10, 44, 15,
     "Biology 5%, Psychology 65%, Sociology 30%"),
]
for s in MCAT_SECTIONS:
    c.execute("INSERT INTO mcat_sections(name,total_questions,passages,passage_based,discrete,content_breakdown) VALUES (?,?,?,?,?,?)", s)

QUESTION_TYPES = [
    ("Question format", "Discrete (stand-alone) question",
     "A single, free-standing question with no associated passage. Tests recall/application of one science concept.",
     "15 per science section; 0 in CARS", "bio2021-2022.pdf; p_physics_and_math.epub"),
    ("Question format", "Passage-based question",
     "A question tied to a reading passage, often with figures, tables, or experimental data.",
     "44 per science section; all 53 in CARS", "bio2021-2022.pdf; critical_reasoning.epub"),

    ("Science reasoning skill", "Skill 1: Knowledge of Scientific Concepts and Principles",
     "Recall, identify, and apply basic science facts, definitions, and relationships.",
     "35% of science-section questions", "bio2021-2022.pdf"),
    ("Science reasoning skill", "Skill 2: Scientific Reasoning and Problem-Solving",
     "Multi-step critical thinking; integrate passage facts with outside content; predict experiment results.",
     "45% of science-section questions", "bio2021-2022.pdf"),
    ("Science reasoning skill", "Skill 3: Reasoning about the Design and Execution of Research",
     "Critically appraise experimental design, controls, methodology, and conclusions.",
     "20% of science-section questions", "bio2021-2022.pdf"),
    ("Science reasoning skill", "Skill 4: Data-Based and Statistical Reasoning",
     "Interpret graphs, tables, statistics, and data to draw conclusions.",
     "5% of science-section questions", "bio2021-2022.pdf"),

    ("CARS skill", "Foundations of Comprehension",
     "Understand basic passage components: main idea, detail, function, definition-in-context.",
     "30% of CARS questions", "critical_reasoning.epub; bio2021-2022.pdf"),
    ("CARS skill", "Reasoning Within the Text",
     "Integrate passage information: inference, strengthen-weaken (within passage), and other within-text reasoning.",
     "30% of CARS questions", "critical_reasoning.epub; bio2021-2022.pdf"),
    ("CARS skill", "Reasoning Beyond the Text",
     "Apply/extrapolate passage ideas to new contexts: apply questions and strengthen-weaken (beyond passage).",
     "40% of CARS questions", "critical_reasoning.epub; bio2021-2022.pdf"),

    ("CARS sub-type", "Main Idea question", "Identify the central thesis or primary purpose of a passage.", None, "critical_reasoning.epub"),
    ("CARS sub-type", "Detail question", "Locate and recall a specific fact stated in the passage.", None, "critical_reasoning.epub"),
    ("CARS sub-type", "Function question", "Explain why the author included a word, sentence, or paragraph.", None, "critical_reasoning.epub"),
    ("CARS sub-type", "Definition-in-Context question", "Determine the meaning of a word/phrase as used in the passage.", None, "critical_reasoning.epub"),
    ("CARS sub-type", "Inference question", "Draw a conclusion implied but not explicitly stated in the passage.", None, "critical_reasoning.epub"),
    ("CARS sub-type", "Strengthen-Weaken (Within the Passage) question",
     "Identify which answer strengthens/weakens a claim based on passage information.", None, "critical_reasoning.epub"),
    ("CARS sub-type", "Apply question", "Apply passage ideas to a new situation or scenario.", None, "critical_reasoning.epub"),
    ("CARS sub-type", "Strengthen-Weaken (Beyond the Passage) question",
     "Use new information from answer choices to strengthen or weaken the author's argument.", None, "critical_reasoning.epub"),

    ("Book practice", "MCAT Concept Check",
     "Open-ended self-assessment questions at the end of each content section.",
     None, "bio2021-2022.pdf; genchem2019-2020.pdf; kphys_and_math.epub"),
    ("Book practice", "Discrete Practice Question",
     "Stand-alone multiple-choice question with answers and explanations at chapter end.",
     None, "bio2021-2022.pdf; genchem2019-2020.pdf"),
    ("Book practice", "Passage-based Practice Question",
     "Chapter-end question tied to a passage, with answers and explanations.",
     None, "bio2021-2022.pdf; kphys_and_math.epub"),
    ("Book practice", "Freestanding Practice Question",
     "Princeton Review term for a discrete, stand-alone practice question.",
     None, "p_physics_and_math.epub"),
    ("Book practice", "Practice Passage",
     "A full passage with associated questions used for practice in review books.",
     None, "p_physics_and_math.epub"),
]
for qt in QUESTION_TYPES:
    c.execute("INSERT INTO question_types(category,name,description,frequency,source) VALUES (?,?,?,?,?)", qt)

def add_kp(subject, source, chapters):
    """chapters: list of (chapter_title, [(section_number, topic), ...])."""
    for ch_title, topics in chapters:
        if not topics:
            c.execute("INSERT INTO knowledge_points(subject,chapter,topic,source) VALUES (?,?,?,?)",
                      (subject, ch_title, ch_title, source))
        else:
            for sn, topic in topics:
                c.execute("INSERT INTO knowledge_points(subject,chapter,section_number,topic,source) VALUES (?,?,?,?,?)",
                          (subject, ch_title, sn or None, topic, source))

BIO = "bio2021-2022.pdf"
add_kp("Biology", BIO, [
    ("The Cell", [("1.1","Cell Theory"),("1.2","Eukaryotic Cells"),
        ("1.3","Classification and Structure of Prokaryotic Cells"),
        ("1.4","Genetics and Growth of Prokaryotic Cells"),
        ("1.5","Viruses and Subviral Particles")]),
    ("Reproduction", [("2.1","The Cell Cycle and Mitosis"),("2.2","Meiosis"),("2.3","The Reproductive System")]),
    ("Embryogenesis and Development", [("3.1","Early Developmental Stages"),("3.2","Mechanisms of Development"),
        ("3.3","Fetal Circulation"),("3.4","Gestation and Birth")]),
    ("The Nervous System", [("4.1","Cells of the Nervous System"),("4.2","Transmission of Neural Impulses"),
        ("4.3","Organization of the Human Nervous System")]),
    ("The Endocrine System", [("5.1","Mechanisms of Hormone Action"),("5.2","Endocrine Organs and Hormones")]),
    ("The Respiratory System", [("6.1","Anatomy and Mechanism of Breathing"),("6.2","Functions of the Respiratory System")]),
    ("The Cardiovascular System", [("7.1","Anatomy of the Cardiovascular System"),("7.2","Blood"),
        ("7.3","Physiology of the Cardiovascular System")]),
    ("The Immune System", [("8.1","Structure of the Immune System"),("8.2","The Innate Immune System"),
        ("8.3","The Adaptive Immune System"),("8.4","The Lymphatic System")]),
    ("The Digestive System", [("9.1","Anatomy of the Digestive System"),("9.2","Ingestion and Digestion"),
        ("9.3","Accessory Organs of Digestion"),("9.4","Absorption and Defecation")]),
    ("Homeostasis", [("10.1","The Excretory System"),("10.2","Skin")]),
    ("The Musculoskeletal System", [("11.1","The Muscular System"),("11.2","The Skeletal System")]),
    ("Genetics and Evolution", [("12.1","Fundamental Concepts of Genetics"),("12.2","Changes in the Gene Pool"),
        ("12.3","Analytical Approaches in Genetics"),("12.4","Evolution")]),
])

GENCHem_K = "genchem2019-2020.pdf"
add_kp("General Chemistry", GENCHem_K, [
    ("Atomic Structure", [("1.1","Subatomic Particles"),("1.2","Atomic Mass vs. Atomic Weight"),
        ("1.3","Rutherford, Planck, and Bohr"),("1.4","Quantum Mechanical Model of Atoms")]),
    ("The Periodic Table", [("2.1","The Periodic Table"),("2.2","Types of Elements"),
        ("2.3","Periodic Properties of the Elements"),("2.4","The Chemistry of Groups")]),
    ("Bonding and Chemical Interactions", [("3.1","Bonding"),("3.2","Ionic Bonds"),
        ("3.3","Covalent Bonds"),("3.4","Intermolecular Forces")]),
    ("Compounds and Stoichiometry", [("4.1","Molecules and Moles"),("4.2","Representation of Compounds"),
        ("4.3","Types of Chemical Reactions"),("4.4","Balancing Chemical Equations"),
        ("4.5","Applications of Stoichiometry"),("4.6","Ions")]),
    ("Chemical Kinetics", [("5.1","Chemical Kinetics"),("5.2","Reaction Rates")]),
    ("Equilibrium", [("6.1","Equilibrium"),("6.2","Le Chatelier's Principle"),("6.3","Kinetic and Thermodynamic Control")]),
    ("Thermochemistry", [("7.1","Systems and Processes"),("7.2","States and State Functions"),("7.3","Heat"),
        ("7.4","Enthalpy"),("7.5","Entropy"),("7.6","Gibbs Free Energy")]),
    ("The Gas Phase", [("8.1","The Gas Phase"),("8.2","Ideal Gases"),("8.3","Kinetic Molecular Theory"),("8.4","Real Gases")]),
    ("Solutions", [("9.1","Nature of Solutions"),("9.2","Concentration"),("9.3","Solution Equilibria"),("9.4","Colligative Properties")]),
    ("Acids and Bases", [("10.1","Definitions"),("10.2","Properties"),("10.3","Polyvalence and Normality"),("10.4","Titration and Buffers")]),
    ("Oxidation-Reduction Reactions", [("11.1","Oxidation-Reduction Reactions"),("11.2","Net Ionic Equations")]),
    ("Electrochemistry", [("12.1","Electrochemical Cells"),("12.2","Cell Potentials"),("12.3","Electromotive Force and Thermodynamics")]),
])

GENCHem_B = "genchem.pdf"
add_kp("General Chemistry", GENCHem_B, [
    ("Section I: Stoichiometry", [("", "Unit Conversion / Dimensional Analysis"),
        ("", "Density Determination"), ("", "Elemental Analysis (mass percent, empirical/molecular formulas, combustion analysis)"),
        ("", "Solution Concentration (molarity, molality, mass percent, density)"),
        ("", "Dilution"), ("", "Beer's Law"),
        ("", "Balancing Reactions and Limiting Reagents"), ("", "Reaction Types and Oxidation States")]),
    ("Section II: Atomic Theory", []),
    ("Section III: Equilibrium", []),
    ("Section IV: Acids & Bases", []),
    ("Section V: Buffers & Titrations", []),
])

PHYS_K = "kphys_and_math.epub"
add_kp("Physics", PHYS_K, [
    ("Kinematics and Dynamics", [("1.1","Units"),("1.2","Vectors and Scalars"),("1.3","Displacement and Velocity"),
        ("1.4","Forces and Acceleration"),("1.5","Newton's Laws"),("1.6","Motion with Constant Acceleration"),
        ("1.7","Mechanical Equilibrium")]),
    ("Work and Energy", [("2.1","Energy"),("2.2","Work"),("2.3","Mechanical Advantage")]),
    ("Thermodynamics", [("3.1","Zeroth Law of Thermodynamics"),("3.2","Systems"),
        ("3.3","First Law of Thermodynamics"),("3.4","Second Law of Thermodynamics and Entropy")]),
    ("Fluids", [("4.1","Characteristics of Fluids and Solids"),("4.2","Hydrostatics"),
        ("4.3","Fluid Dynamics"),("4.4","Fluids in Physiology")]),
    ("Electrostatics and Magnetism", [("5.1","Charges"),("5.2","Coulomb's Law"),("5.3","Electrical Potential Energy"),
        ("5.4","Electrical Potential"),("5.5","Special Cases in Electrostatics"),("5.6","Magnetism")]),
    ("Circuits", [("6.1","Current"),("6.2","Resistance"),("6.3","Capacitance and Capacitors"),("6.4","Meters")]),
    ("Waves and Sound", [("7.1","General Wave Characteristics"),("7.2","Sound")]),
    ("Light and Optics", [("8.1","Electromagnetic Spectrum"),("8.2","Geometrical Optics"),
        ("8.3","Diffraction"),("8.4","Polarization")]),
    ("Atomic and Nuclear Phenomena", [("9.1","The Photoelectric Effect"),("9.2","Absorption and Emission of Light"),
        ("9.3","Nuclear Binding Energy and Mass Defect"),("9.4","Nuclear Reactions")]),
    ("Mathematics", [("10.1","Arithmetic and Significant Figures"),("10.2","Exponents and Logarithms"),
        ("10.3","Trigonometry"),("10.4","Problem-Solving")]),
    ("Reasoning About the Design and Execution of Research", [("11.1","The Scientific Method"),
        ("11.2","Basic Science Research"),("11.3","Human Subjects Research"),("11.4","Ethics"),
        ("11.5","Research in the Real World")]),
    ("Data-Based and Statistical Reasoning", [("12.1","Measures of Central Tendency"),("12.2","Distributions"),
        ("12.3","Measures of Distribution"),("12.4","Probability"),("12.5","Statistical Testing"),
        ("12.6","Charts, Graphs, and Tables"),("12.7","Applying Data")]),
])

PHYS_P = "p_physics_and_math.epub"
add_kp("Physics", PHYS_P, [
    ("MCAT 2015 Basics", []),
    ("Physics Strategy for the MCAT", [("2.1","General Science Sections Overview"),("2.2","General Science Passage Types"),
        ("2.3","General Science Question Types"),("2.4","Physics on the MCAT"),("2.5","Tackling a Passage"),
        ("2.6","Physics Question Types")]),
    ("Kinematics", [("3.1","Units and Dimensions"),("3.2","Kinematics"),("3.3","Uniformly Accelerated Motion"),
        ("3.4","Kinematics with Graphs"),("3.5","Free Fall"),("3.6","Projectile Motion")]),
    ("Mechanics I", [("4.1","Mass, Force, and Newton's Laws"),("4.2","Newton's Law of Gravitation"),("4.3","Friction"),
        ("4.4","Inclined Planes"),("4.5","Pulleys")]),
    ("Mechanics II", [("5.1","Center of Mass"),("5.2","Uniform Circular Motion"),("5.3","Torque"),
        ("5.4","Equilibrium"),("5.5","Rotational Inertia")]),
    ("Mechanics III", [("6.1","Work"),("6.2","Power"),("6.3","Kinetic Energy"),("6.4","Potential Energy"),
        ("6.5","Total Mechanical Energy"),("6.6","Simple Machines and Mechanical Advantage"),
        ("6.7","Momentum"),("6.8","A Note on Angular Momentum")]),
    ("Thermodynamics", [("7.1","Systems, Thermal Physics, and Thermodynamics"),("7.2","The Zeroth Law of Thermodynamics"),
        ("7.3","The First Law of Thermodynamics"),("7.4","The Second Law of Thermodynamics")]),
    ("Fluids and Elasticity of Solids", [("8.1","Hydrostatics: Fluids at Rest"),("8.2","Hydrodynamics: Fluids in Motion"),
        ("8.3","The Elasticity of Solids")]),
    ("Electrostatics", [("9.1","Electric Charge"),("9.2","Electric Force and Coulomb's Law"),("9.3","Electric Fields"),
        ("9.4","Electric Potential and Potential Energy")]),
    ("Electricity and Magnetism", [("10.1","Electric Circuits"),("10.2","Capacitors"),("10.3","Alternating Current"),
        ("10.4","Magnetic Fields and Forces")]),
    ("Oscillations and Waves", [("11.1","Oscillations"),("11.2","Waves"),("11.3","Interference of Waves"),("11.4","Standing Waves")]),
    ("Sound", [("12.1","Sound Waves"),("12.2","Standing Sound Waves in Tubes"),("12.3","Beats"),
        ("12.4","Intensity and Intensity Level"),("12.5","The Doppler Effect")]),
    ("Light and Geometrical Optics", [("13.1","Electromagnetic Waves"),("13.2","Reflection and Refraction"),
        ("13.3","Wave Effects"),("13.4","Mirrors"),("13.5","Lenses")]),
    ("Quantum Physics", [("14.1","Quantization"),("14.2","The Bohr Model of the Atom"),("14.3","The Pauli Exclusion Principle"),
        ("14.4","The Photoelectric Effect"),("14.5","The Heisenberg Uncertainty Principle")]),
    ("Arithmetic, Algebra, and Graphs", [("15.1","The Importance of Approximation"),
        ("15.2","Scientific Notation, Exponents, and Radicals"),("15.3","Fractions, Ratios, and Percents"),
        ("15.4","Equations and Inequalities"),("15.5","The x-y Plane, Lines, and Other Graphs")]),
    ("Trigonometry", [("16.1","Introduction"),("16.2","Extending the Definitions"),
        ("16.3","Inverse Trigonometry Functions"),("16.4","Radian Measure")]),
    ("Vectors", [("17.1","Scalars and Vectors"),("17.2","Operations with Vectors"),("17.3","Vector Projections and Components")]),
    ("Proportions", [("18.1","Direct Proportions"),("18.2","Inverse Proportions")]),
    ("Logarithms", [("19.1","The Definition of a Logarithm"),("19.2","Laws of Logarithms")]),
])

CARS = "critical_reasoning.epub"
add_kp("Critical Analysis and Reasoning Skills (CARS)", CARS, [
    ("About CARS", [("1.1","The CARS Section"),("1.2","Passages"),("1.3","Question Categories")]),
    ("Analyzing Rhetoric", [("2.1","What Is Rhetoric?"),("2.2","Key Components of Rhetoric"),("2.3","Rhetorical Analysis")]),
    ("Keywords", [("3.1","Reading Strategically with Keywords"),("3.2","Relation Keywords"),
        ("3.3","Author Keywords"),("3.4","Logic Keywords")]),
    ("Outlining the Passage", [("4.1","The Kaplan Method for CARS Passages"),
        ("4.2","Reverse-Engineering the Author's Outline"),("4.3","Practicing the Strategy")]),
    ("Dissecting Arguments", [("5.1","Domains of Discourse"),("5.2","Concepts: The Basic Elements of Logic"),
        ("5.3","Claims: The Bearers of Truth Value"),("5.4","Arguments: Conclusions and Evidence")]),
    ("Formal Logic", [("6.1","The Logic of Conditionals"),("6.2","Applications of Conditionals"),("6.3","Analogical Reasoning")]),
    ("Understanding Passages", [("7.1","Varieties of Passages"),("7.2","Support in Passages"),("7.3","Anticipating Questions")]),
    ("Question and Answer Strategy", [("8.1","Kaplan Method for CARS Questions"),
        ("8.2","Wrong Answer Pathologies"),("8.3","Signs of a Healthy Answer")]),
    ("Question Types I: Foundations of Comprehension", [("9.1","Main Idea Questions"),("9.2","Detail Questions"),
        ("9.3","Function Questions"),("9.4","Definition-in-Context Questions")]),
    ("Question Types II: Reasoning Within the Text", [("10.1","Inference Questions"),
        ("10.2","Strengthen-Weaken (Within the Passage) Questions"),("10.3","Other Reasoning Within the Text Questions")]),
    ("Question Types III: Reasoning Beyond the Text", [("11.1","Apply Questions"),
        ("11.2","Strengthen-Weaken (Beyond the Passage) Questions"),("11.3","Other Reasoning Beyond the Text Questions")]),
    ("Effective Review of CARS", []),
])

# McGraw-Hill Chem/Phys foundations book
add_kp("General Chemistry", "chembio.pdf", [
    ("Chemical and Physical Foundations of Biological Systems", [
        ("", "General chemistry topics for the Chem/Phys section")])])
add_kp("Physics", "chembio.pdf", [
    ("Chemical and Physical Foundations of Biological Systems", [
        ("", "Physics topics for the Chem/Phys section")])])

# Next Step QBook question bank
for subj in ["Biology", "General Chemistry", "Organic Chemistry", "Physics", "Biochemistry"]:
    c.execute("INSERT INTO knowledge_points(subject,topic,source) VALUES (?,?,?)",
              (subj, "Discrete and passage-based practice questions (2,000+ question bank)", "qbook_2000.pdf"))

conn.commit()

# --- report ---
for tbl in ["subjects", "sources", "mcat_sections", "question_types", "knowledge_points"]:
    n = c.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    print(f"{tbl}: {n} rows")

conn.close()
print("DB written to", DB)





