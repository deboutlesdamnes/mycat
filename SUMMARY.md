# MyCat Corpus — Question Types & Knowledge Points

The `corpus/` folder contains **8 MCAT (Medical College Admission Test) study
materials from 5 publishers** (Kaplan, McGraw-Hill, The Berkeley Review,
The Princeton Review, and Next Step Pre-Med).

## Sources (documents)

| File | Title | Publisher | Format | Focus |
|------|-------|-----------|--------|-------|
| `bio2021-2022.pdf` | Kaplan MCAT Biology Review 2021–2022 | Kaplan | PDF | Biology |
| `chembio.pdf` | MCAT Chemical & Physical Foundations of Biological Systems 2015 | McGraw-Hill | PDF | Chemistry & Physics |
| `critical_reasoning.epub` | Kaplan MCAT Critical Analysis & Reasoning Skills Review | Kaplan | EPUB | CARS |
| `genchem.pdf` | General Chemistry Part I (Sections I–V) | The Berkeley Review | PDF | General Chemistry |
| `genchem2019-2020.pdf` | Kaplan MCAT General Chemistry Review 2019–2020 | Kaplan | PDF | General Chemistry |
| `kphys_and_math.epub` | Kaplan MCAT Physics and Math Review | Kaplan | EPUB | Physics & Math |
| `p_physics_and_math.epub` | MCAT Physics and Math Review (New for MCAT 2015) | The Princeton Review | EPUB | Physics & Math |
| `qbook_2000.pdf` | MCAT QBook (2,000+ questions) | Next Step Pre-Med | PDF | All science topics |

## Question Types

### 1. By format
- **Discrete / stand-alone (freestanding) question** — no passage; tests one science concept.
- **Passage-based question** — tied to a passage, often with figures/tables/experimental data.

### 2. Science-section reasoning skills (4 skills)
| Skill | % of science questions |
|-------|------------------------|
| Skill 1: Knowledge of Scientific Concepts and Principles | 35% |
| Skill 2: Scientific Reasoning and Problem-Solving | 45% |
| Skill 3: Reasoning about the Design and Execution of Research | 20% |
| Skill 4: Data-Based and Statistical Reasoning | 5% |

### 3. CARS skills (3 skills + sub-types)
| CARS skill | % of CARS questions | Sub-types |
|------------|---------------------|-----------|
| Foundations of Comprehension | 30% | Main Idea, Detail, Function, Definition-in-Context |
| Reasoning Within the Text | 30% | Inference, Strengthen–Weaken (Within), Other |
| Reasoning Beyond the Text | 40% | Apply, Strengthen–Weaken (Beyond), Other |

### 4. Book-internal practice question types
- **MCAT Concept Checks** (open-ended, end of each section)
- **Discrete Practice Questions** (stand-alone, with answers & explanations)
- **Passage-based Practice Questions** (passage-tied, with answers & explanations)
- **Freestanding Practice Questions** (Princeton Review term for discrete)
- **Practice Passages** (full passage + questions)

## MCAT Exam Sections (structure)

| Section | Total Q | Passages | Passage-based | Discrete | Content breakdown |
|---------|---------|----------|---------------|----------|-------------------|
| Chemical & Physical Foundations of Biological Systems (Chem/Phys) | 59 | 10 | 44 | 15 | Biochem 25%, Bio 5%, Gen Chem 30%, OChem 15%, Physics 25% |
| Critical Analysis and Reasoning Skills (CARS) | 53 | 9 | 53 | 0 | Humanities 50%, Social Sciences 50% |
| Biological & Biochemical Foundations of Living Systems (Bio/Biochem) | 59 | 10 | 44 | 15 | Bio 65%, Biochem 25%, Gen Chem 5%, OChem 5% |
| Psychological, Social, and Biological Foundations of Behavior (Psych/Soc) | 59 | 10 | 44 | 15 | Bio 5%, Psych 65%, Soc 30% |

## Knowledge Points (by subject)

### Biology (Kaplan, 12 chapters)
The Cell · Reproduction · Embryogenesis and Development · The Nervous System ·
The Endocrine System · The Respiratory System · The Cardiovascular System ·
The Immune System · The Digestive System · Homeostasis · The Musculoskeletal
System · Genetics and Evolution

### General Chemistry (Kaplan, 12 chapters)
Atomic Structure · The Periodic Table · Bonding and Chemical Interactions ·
Compounds and Stoichiometry · Chemical Kinetics · Equilibrium · Thermochemistry ·
The Gas Phase · Solutions · Acids and Bases · Oxidation–Reduction Reactions ·
Electrochemistry

### General Chemistry (The Berkeley Review, Part I — 5 sections)
Stoichiometry · Atomic Theory · Equilibrium · Acids & Bases · Buffers & Titrations

### Physics & Mathematics (Kaplan, 12 chapters)
Kinematics and Dynamics · Work and Energy · Thermodynamics · Fluids ·
Electrostatics and Magnetism · Circuits · Waves and Sound · Light and Optics ·
Atomic and Nuclear Phenomena · Mathematics · Reasoning About the Design and
Execution of Research · Data-Based and Statistical Reasoning

### Physics & Mathematics (Princeton Review, 19 chapters)
MCAT 2015 Basics · Physics Strategy · Kinematics · Mechanics I/II/III ·
Thermodynamics · Fluids and Elasticity · Electrostatics · Electricity and
Magnetism · Oscillations and Waves · Sound · Light and Geometrical Optics ·
Quantum Physics · Arithmetic/Algebra/Graphs · Trigonometry · Vectors ·
Proportions · Logarithms

### Critical Analysis & Reasoning Skills (Kaplan, 12 chapters)
About CARS · Analyzing Rhetoric · Keywords · Outlining the Passage · Dissecting
Arguments · Formal Logic · Understanding Passages · Question and Answer
Strategy · Question Types I (Foundations of Comprehension) · Question Types II
(Reasoning Within the Text) · Question Types III (Reasoning Beyond the Text) ·
Effective Review of CARS

### Question bank (Next Step QBook)
2,000+ discrete and passage-based questions across Biology, General Chemistry,
Organic Chemistry, Physics, and Biochemistry.

## Database

The structured summary is stored in **`mycat_knowledge.db`** (SQLite) with these tables:

- `subjects` (9 rows)
- `sources` (8 rows)
- `mcat_sections` (4 rows)
- `question_types` (22 rows)
- `knowledge_points` (275 rows)
