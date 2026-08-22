// Original, simulated MCAT-style practice questions (not copied from AAMC or
// any copyrighted source) organized into 6 decks covering the four tested
// MCAT sections: Bio/Biochem, Chem/Phys, Psych/Soc, and CARS.

const DECKS = [
  {
    id: "set1",
    title: "Deck 1",
    section: "Biological & Biochemical Foundations",
    questions: [
      {
        question: "The 'committed step' of a metabolic pathway is best described as one that is:",
        options: [
          "Reversible and near equilibrium",
          "Typically irreversible and rate-limiting, serving as a key regulatory point",
          "The pathway's final step by definition",
          "Independent of allosteric regulation"
        ],
        correct: 1,
        explanation: "Committed steps (e.g., PFK-1 in glycolysis) are strongly exergonic, essentially irreversible reactions catalyzed by allosterically regulated enzymes, making them the pathway's primary control points."
      },
      {
        question: "During oxidative phosphorylation, the proton-motive force across the inner mitochondrial membrane primarily drives:",
        options: [
          "Reduction of NAD+ to NADH",
          "ATP synthase to phosphorylate ADP",
          "Electron transport through Complex IV",
          "Conversion of pyruvate to acetyl-CoA"
        ],
        correct: 1,
        explanation: "Chemiosmotic coupling: the H+ gradient built by the electron transport chain flows back through ATP synthase, driving ADP + Pi → ATP."
      },
      {
        question: "A point mutation that converts a sense codon into a stop codon is classified as a:",
        options: ["Silent mutation", "Missense mutation", "Nonsense mutation", "Frameshift mutation"],
        correct: 2,
        explanation: "Nonsense mutations introduce a premature stop codon, typically truncating and often inactivating the protein — distinct from missense (different amino acid), silent (same amino acid), or frameshift (insertion/deletion) mutations."
      },
      {
        question: "In the HPA axis, cortisol released from the adrenal cortex primarily acts to:",
        options: [
          "Stimulate further release of CRH and ACTH",
          "Inhibit hypothalamic CRH and pituitary ACTH release via negative feedback",
          "Directly increase blood glucose without affecting the hypothalamus or pituitary",
          "Have no regulatory effect upstream"
        ],
        correct: 1,
        explanation: "Cortisol feeds back on the hypothalamus and anterior pituitary to suppress CRH and ACTH release, a classic negative feedback loop."
      },
      {
        question: "A Southern blot is used to detect and analyze fragments of:",
        options: ["RNA", "DNA", "Protein", "Lipid"],
        correct: 1,
        explanation: "Southern blotting targets DNA; Northern blotting targets RNA; Western blotting targets protein — a common mnemonic ordering worth memorizing."
      }
    ]
  },
  {
    id: "set2",
    title: "Deck 2",
    section: "Chemical & Physical Foundations",
    questions: [
      {
        question: "Decreasing the volume of a gas-phase equilibrium system (increasing pressure) shifts the equilibrium toward:",
        options: [
          "The side with more moles of gas",
          "The side with fewer moles of gas",
          "No shift occurs",
          "A shift determined only by temperature"
        ],
        correct: 1,
        explanation: "By Le Chatelier's principle, compressing the volume increases pressure, so the system shifts toward the side with fewer gas moles to partially relieve that pressure."
      },
      {
        question: "A block slides down a frictionless incline. Which quantity remains constant throughout the descent?",
        options: ["Kinetic energy", "Potential energy", "Total mechanical energy", "Velocity"],
        correct: 2,
        explanation: "With no friction, mechanical energy (KE + PE) is conserved even though KE and PE individually change as the block descends."
      },
      {
        question: "Mixing equal moles of a weak acid and its conjugate base produces a solution with pH approximately equal to:",
        options: ["7", "The pKa of the acid", "The pKb of the conjugate base", "0"],
        correct: 1,
        explanation: "By the Henderson–Hasselbalch equation, pH = pKa + log([A⁻]/[HA]); with equal concentrations the ratio is 1, log(1) = 0, so pH = pKa."
      },
      {
        question: "A converging lens forms a real, inverted image when the object is placed:",
        options: [
          "Between the lens and the focal point",
          "Exactly at the focal point",
          "Beyond the focal point",
          "Only at infinity"
        ],
        correct: 2,
        explanation: "An object placed beyond the focal length of a converging lens produces a real, inverted image; placed within the focal length, it produces a virtual, upright, magnified image instead."
      },
      {
        question: "In a redox reaction, the oxidizing agent is the species that:",
        options: [
          "Loses electrons and is itself oxidized",
          "Gains electrons and is itself reduced",
          "Donates protons to the other species",
          "Remains chemically unchanged"
        ],
        correct: 1,
        explanation: "An oxidizing agent causes another species to be oxidized by accepting electrons from it — in doing so, the oxidizing agent itself is reduced."
      }
    ]
  },
  {
    id: "set3",
    title: "Deck 3",
    section: "Organic Chemistry & Biochemistry",
    questions: [
      {
        question: "Isomers with identical connectivity that differ only in spatial arrangement around a double bond or ring are called:",
        options: ["Constitutional isomers", "Cis-trans (geometric) isomers", "Enantiomers", "Conformational isomers"],
        correct: 1,
        explanation: "Cis-trans isomerism arises from restricted rotation around a double bond or ring; the connectivity is identical but spatial arrangement differs — distinct from enantiomers (non-superimposable mirror images) or constitutional isomers (different connectivity)."
      },
      {
        question: "In an SN2 reaction, the nucleophile attacks the electrophilic carbon:",
        options: [
          "From the same side as the leaving group, causing retention of configuration",
          "From the side opposite the leaving group, causing inversion of configuration",
          "From a random direction with no stereochemical consequence",
          "Only after the leaving group has fully departed"
        ],
        correct: 1,
        explanation: "SN2 reactions proceed via a single concerted, backside attack, producing a Walden inversion of stereochemistry at the reactive carbon."
      },
      {
        question: "At an amino acid's isoelectric point (pI), the molecule:",
        options: [
          "Carries maximum net positive charge",
          "Carries maximum net negative charge",
          "Exists predominantly as a zwitterion with net charge of zero",
          "Is fully deprotonated at every ionizable group"
        ],
        correct: 2,
        explanation: "At the pI, the amino acid's average net charge is zero — it exists predominantly in its zwitterionic form, with both a protonated amine and deprotonated carboxylate."
      },
      {
        question: "Which technique is most useful for identifying the number of distinct hydrogen environments within an organic molecule?",
        options: ["IR spectroscopy", "UV-Vis spectroscopy", "¹H NMR spectroscopy", "Mass spectrometry"],
        correct: 2,
        explanation: "¹H NMR resolves distinct proton environments as separate peaks with characteristic chemical shifts; IR is better suited to identifying functional groups, and MS to molecular mass/fragmentation."
      },
      {
        question: "A protein's secondary structure refers to:",
        options: [
          "The linear sequence of amino acids",
          "Local folding patterns such as alpha helices and beta sheets",
          "The overall three-dimensional shape from all interactions",
          "The assembly of multiple polypeptide subunits"
        ],
        correct: 1,
        explanation: "Secondary structure describes local, repeating hydrogen-bonding patterns (alpha helices, beta sheets). Primary structure is sequence, tertiary is overall 3D fold, and quaternary is multi-subunit assembly."
      }
    ]
  },
  {
    id: "set4",
    title: "Deck 4",
    section: "Psychological, Social & Biological Foundations of Behavior",
    questions: [
      {
        question: "The biopsychosocial model explains health outcomes primarily as a result of:",
        options: [
          "Biological factors alone",
          "The interaction of biological, psychological, and social factors",
          "Social factors alone, independent of biology",
          "Largely random, unpredictable processes"
        ],
        correct: 1,
        explanation: "The biopsychosocial model, a recurring MCAT theme, holds that health and behavior emerge from the interplay of biological, psychological, and social/environmental factors, not any one domain alone."
      },
      {
        question: "The concept of the 'looking-glass self' — that self-concept develops from perceiving how others judge us — is most associated with:",
        options: ["Sigmund Freud", "Charles Horton Cooley", "Erik Erikson", "B.F. Skinner"],
        correct: 1,
        explanation: "Cooley's looking-glass self describes how individuals form their self-image based on how they imagine others perceive and evaluate them."
      },
      {
        question: "Removing an unpleasant stimulus immediately after a desired behavior, increasing that behavior's frequency, is an example of:",
        options: ["Positive reinforcement", "Negative reinforcement", "Positive punishment", "Negative punishment"],
        correct: 1,
        explanation: "Negative reinforcement increases a behavior's frequency by removing an aversive stimulus — distinct from punishment (which decreases behavior) and positive reinforcement (which adds a pleasant stimulus)."
      },
      {
        question: "A system of social stratification assigning status at birth, with little to no mobility between strata, is best described as a:",
        options: ["Class system", "Caste system", "Meritocracy", "Egalitarian system"],
        correct: 1,
        explanation: "Caste systems assign social status at birth with minimal mobility, in contrast to class systems, which allow some movement based on achieved status such as wealth or education."
      },
      {
        question: "Which brain structure is most closely associated with consolidating new long-term declarative memories?",
        options: ["Amygdala", "Hippocampus", "Cerebellum", "Medulla oblongata"],
        correct: 1,
        explanation: "The hippocampus plays a central role in consolidating new explicit/declarative memories; the amygdala is more tied to emotional memory, and the cerebellum to procedural/motor learning."
      }
    ]
  },
  {
    id: "set5",
    title: "Deck 5",
    section: "CARS (Critical Analysis & Reasoning Skills)",
    passage: "Economists have long debated whether technological unemployment — job loss driven specifically by automation — represents a temporary transitional cost or a permanent structural shift in labor markets. Historical episodes, such as the mechanization of agriculture, eventually gave way to net job creation in new sectors, a pattern often cited by optimists who view current anxieties over artificial intelligence as overstated. Critics counter that previous transitions unfolded over generations, allowing institutions and workers time to adapt, whereas contemporary automation compresses this timeline dramatically, leaving little room for retraining or gradual absorption into new industries. Moreover, earlier transitions primarily displaced physical labor, while current automation increasingly encroaches on cognitive tasks once considered uniquely human, raising the question of whether any labor category will remain reliably insulated from displacement.",
    questions: [
      {
        question: "The passage's central tension is best described as a disagreement over:",
        options: [
          "Whether automation causes any job loss at all",
          "Whether historical patterns of labor market adaptation will repeat under current conditions",
          "Whether AI is more advanced than previous technologies",
          "Whether governments should regulate automation"
        ],
        correct: 1,
        explanation: "The passage frames a debate between optimists (who expect history to repeat) and critics (who argue current conditions differ meaningfully from past transitions) — the disagreement is about whether the historical pattern still applies."
      },
      {
        question: "According to the passage, the critics primarily emphasize which distinction between past and present automation?",
        options: [
          "Past automation was voluntary; current automation is not",
          "Past transitions occurred slowly enough for adaptation; current ones are compressed",
          "Past automation affected only agriculture",
          "Current automation is reversible while past automation was not"
        ],
        correct: 1,
        explanation: "The passage states critics stress that earlier transitions 'unfolded over generations,' while current automation 'compresses this timeline dramatically' — a difference in pace and adaptation time, not reversibility or voluntariness."
      },
      {
        question: "The author's tone toward the 'optimist' position can best be characterized as:",
        options: [
          "Fully endorsing it",
          "Dismissively rejecting it",
          "Presenting it evenhandedly alongside a counterargument",
          "Ridiculing it as historically naive"
        ],
        correct: 2,
        explanation: "The passage presents the optimist view and then the critics' counterargument without endorsing either side outright, a neutral, expository tone typical of CARS passages."
      },
      {
        question: "Which of the following, if true, would most strengthen the critics' argument as presented in the passage?",
        options: [
          "Historically, new industries took decades to absorb workers displaced by mechanization",
          "Retraining programs have become more effective in recent years",
          "Today's automation primarily targets manual, not cognitive, labor",
          "Historical labor transitions also happened very rapidly"
        ],
        correct: 0,
        explanation: "The critics' argument rests on the premise that past transitions were slow enough to allow adaptation; evidence that absorption historically took decades reinforces the contrast with today's much faster automation cycle."
      },
      {
        question: "The passage suggests a key difference in what automation displaces today compared to historically is that:",
        options: [
          "Today's automation displaces fewer jobs overall",
          "Today's automation increasingly affects cognitive, not just physical, labor",
          "Today's automation is limited to agriculture and manufacturing",
          "Today's automation is easier to predict than in the past"
        ],
        correct: 1,
        explanation: "The passage explicitly notes that current automation 'increasingly encroaches on cognitive tasks once considered uniquely human,' unlike earlier transitions that primarily displaced physical labor."
      }
    ]
  },
  {
    id: "set6",
    title: "Deck 6",
    section: "Mixed Review",
    questions: [
      {
        question: "Which type of muscle tissue is striated, involuntary, and connected by intercalated discs?",
        options: ["Skeletal", "Cardiac", "Smooth", "None of the above"],
        correct: 1,
        explanation: "Cardiac muscle uniquely combines striations with involuntary control, and its intercalated discs allow synchronized, coordinated contraction across cells."
      },
      {
        question: "Moving left to right across a period on the periodic table, which property generally increases?",
        options: ["Atomic radius", "Electronegativity", "Metallic character", "Number of electron shells"],
        correct: 1,
        explanation: "Effective nuclear charge increases across a period, increasing electronegativity and ionization energy while atomic radius decreases."
      },
      {
        question: "A charged particle moving through a magnetic field experiences a force that is:",
        options: [
          "Parallel to its velocity",
          "Perpendicular to both its velocity and the magnetic field",
          "Parallel to the magnetic field",
          "Independent of the direction of velocity"
        ],
        correct: 1,
        explanation: "The magnetic force F = qv × B is always perpendicular to both the velocity and the magnetic field, as given by the right-hand rule."
      },
      {
        question: "Attributing another person's failure to internal character flaws while attributing one's own failure to situational circumstances reflects:",
        options: ["Actor-observer bias", "The fundamental attribution error applied only to strangers", "Self-serving bias exclusively", "Confirmation bias"],
        correct: 0,
        explanation: "Actor-observer bias describes this asymmetry: we tend to explain others' behavior dispositionally while explaining our own behavior situationally."
      },
      {
        question: "Competitive enzyme inhibitors typically have which effect on Vmax and apparent Km?",
        options: [
          "Increase Vmax; no change to Km",
          "Increase apparent Km; no change to Vmax",
          "Decrease both Vmax and Km",
          "No effect on either parameter"
        ],
        correct: 1,
        explanation: "Competitive inhibitors bind the active site, competing with substrate. Because the effect can be overcome with excess substrate, Vmax is unchanged, but the apparent Km increases since more substrate is needed to reach half-maximal velocity."
      }
    ]
  }
];
