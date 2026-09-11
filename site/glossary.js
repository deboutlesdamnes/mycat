// site/glossary.js
// MCAT key-concept glossary + hover tooltip engine.
// Included before the page render script on quiz/practice/flashcards/exams
// pages. Exposes window.Glossary = { GLOSSARY, linkify, initTooltips }.
//
// linkify(text) HTML-escapes the input and wraps recognized concepts in
// <span class="concept" data-term="...">, so the page scripts can render
// concept-bearing text safely and consistently. A single delegated tooltip
// element is reused for every concept (mouse, keyboard focus, and touch).
(function () {
  "use strict";

  // ---------------------------------------------------------------------
  // Glossary data. Add entries freely; `aliases` cover alternate
  // spellings/punctuation (en-dash vs hyphen, accented vs unaccented).
  // ---------------------------------------------------------------------
  const GLOSSARY = [
    // ----- Chemistry & Physics -----
    { term: "Henderson–Hasselbalch equation",
      aliases: ["Henderson-Hasselbalch equation", "Henderson–Hasselbalch", "Henderson-Hasselbalch"],
      definition: "pH = pKa + log([A⁻]/[HA]). Relates a buffer's pH to its acid's pKa and the conjugate-base/acid ratio; at the half-equivalence point the ratio is 1, so pH = pKa." },
    { term: "Buffer",
      aliases: ["buffer solution"],
      definition: "A solution of a weak acid and its conjugate base (or a weak base and its conjugate acid) that resists pH changes when small amounts of acid or base are added." },
    { term: "Le Chatelier's principle",
      aliases: ["Le Châtelier's principle", "Le Chatelier principle", "Le Châtelier principle"],
      definition: "When a system at equilibrium is stressed (concentration, pressure/volume, or temperature change), it shifts to partially relieve that stress; only temperature changes alter the equilibrium constant." },
    { term: "Equilibrium constant",
      aliases: ["Keq", "Kc", "Kp", "equilibrium constant (K)"],
      definition: "The ratio of product to reactant concentrations (or pressures), each raised to its stoichiometric coefficient, for a reaction at equilibrium; its magnitude indicates which side is favored." },
    { term: "Reaction quotient",
      aliases: ["reaction quotient (Q)"],
      definition: "The same product/reactant ratio as K but computed at non-equilibrium conditions; comparing Q to K predicts the direction a reaction must shift (Q < K shifts right, Q > K shifts left)." },
    { term: "Rate-determining step",
      aliases: ["rate determining step"],
      definition: "The slowest elementary step in a reaction mechanism; it limits the overall rate and dictates the experimentally observed rate law." },
    { term: "Rate law",
      aliases: ["rate equation"],
      definition: "An experimentally determined equation relating reaction rate to reactant concentrations and a rate constant (rate = k[A]^m[B]^n); reaction orders must be determined experimentally because they can't be read off the balanced equation." },
    { term: "Reaction intermediate",
      aliases: ["intermediate species"],
      definition: "A species produced in one elementary step and consumed in a later one; it does not appear in the overall equation or the final rate law." },
    { term: "Catalyst",
      definition: "A substance that increases reaction rate by lowering activation energy through an alternative mechanism; it is not consumed and does not affect equilibrium or ΔG." },
    { term: "Activation energy",
      aliases: ["Ea", "activation barrier"],
      definition: "The minimum energy reactants must possess to reach the transition state and react; a lower activation energy means a faster reaction." },
    { term: "Enthalpy",
      aliases: ["ΔH"],
      definition: "H = U + PV. At constant pressure, the enthalpy change (ΔH) equals the heat transferred; ΔH < 0 is exothermic and ΔH > 0 is endothermic." },
    { term: "Entropy",
      aliases: ["ΔS"],
      definition: "A measure of energy dispersal or disorder; processes that increase the number of accessible microstates increase entropy (ΔS > 0)." },
    { term: "Gibbs free energy",
      aliases: ["Gibbs energy", "free energy", "ΔG"],
      definition: "ΔG = ΔH − TΔS. A process is spontaneous when ΔG < 0, nonspontaneous when ΔG > 0, and at equilibrium when ΔG = 0." },
    { term: "First law of thermodynamics",
      definition: "Energy is conserved: ΔU = Q − W, where Q is heat added to the system and W is work done by the system." },
    { term: "Zeroth law of thermodynamics",
      definition: "If object A is in thermal equilibrium with B and B with C, then A and C are also in equilibrium; this establishes temperature as the property that determines thermal equilibrium." },
    { term: "Ideal gas law",
      aliases: ["ideal gas"],
      definition: "PV = nRT. Describes a hypothetical gas whose particles have negligible volume and no intermolecular forces." },
    { term: "van der Waals equation",
      aliases: ["van der Waals", "van der Waals equation of state"],
      definition: "Corrects the ideal gas law for real gases: (P + an²/V²)(V − nb) = nRT. It accounts for intermolecular attractions and finite molecular volume." },
    { term: "Intermolecular forces",
      aliases: ["intermolecular force", "IMF"],
      definition: "Attractions between molecules (not within them). From weakest to strongest for comparable size: London dispersion, dipole–dipole, and hydrogen bonding." },
    { term: "Hydrogen bonding",
      aliases: ["hydrogen bond", "hydrogen bonds"],
      definition: "A strong dipole–dipole attraction between a hydrogen atom bonded to N, O, or F and a lone pair on another N, O, or F; explains water's unusually high boiling point." },
    { term: "London dispersion forces",
      aliases: ["dispersion forces", "London forces"],
      definition: "The weakest intermolecular force, arising from transient electron-cloud distortions that create instantaneous dipoles; strength increases with molecular size and polarizability." },
    { term: "Dipole–dipole interactions",
      aliases: ["dipole-dipole interactions", "dipole–dipole forces"],
      definition: "Attractions between the positive end of one polar molecule and the negative end of another." },
    { term: "VSEPR theory",
      definition: "Valence Shell Electron Pair Repulsion: electron groups around a central atom arrange to minimize repulsion, determining molecular geometry (e.g., tetrahedral, trigonal planar, linear)." },
    { term: "Resonance",
      aliases: ["resonance structures"],
      definition: "Two or more valid Lewis structures differing only in electron placement; the true structure is a hybrid with delocalized electrons and bond orders averaged over the forms." },
    { term: "Formal charge",
      definition: "A bookkeeping value: valence electrons minus nonbonding electrons minus half the bonding electrons; the most stable Lewis structures minimize formal charges and place negative charge on more electronegative atoms." },
    { term: "Oxidation",
      aliases: ["oxidized"],
      definition: "Loss of electrons (or an increase in oxidation state); in a redox reaction, oxidation occurs at the anode." },
    { term: "Reduction",
      aliases: ["reduced"],
      definition: "Gain of electrons (or a decrease in oxidation state); in a redox reaction, reduction occurs at the cathode." },
    { term: "Oxidizing agent",
      definition: "The species that is reduced and thereby causes another species to be oxidized." },
    { term: "Reducing agent",
      definition: "The species that is oxidized and thereby causes another species to be reduced." },
    { term: "Galvanic cell",
      aliases: ["voltaic cell"],
      definition: "An electrochemical cell that uses a spontaneous redox reaction to produce electrical energy; oxidation occurs at the anode and reduction at the cathode." },
    { term: "Electrolytic cell",
      definition: "An electrochemical cell that uses external electrical energy to drive a nonspontaneous reaction; oxidation still occurs at the anode and reduction at the cathode." },
    { term: "Brønsted–Lowry acid",
      aliases: ["Brønsted-Lowry acid", "Bronsted-Lowry acid"],
      definition: "A proton (H⁺) donor." },
    { term: "Brønsted–Lowry base",
      aliases: ["Brønsted-Lowry base", "Bronsted-Lowry base"],
      definition: "A proton (H⁺) acceptor." },
    { term: "Brønsted–Lowry definition",
      aliases: ["Brønsted-Lowry definition", "Bronsted-Lowry definition"],
      definition: "Defines acids as proton donors and bases as proton acceptors, broadening the Arrhenius definition to any solvent." },
    { term: "Lewis acid",
      definition: "An electron-pair acceptor." },
    { term: "Lewis base",
      definition: "An electron-pair donor." },
    { term: "Lewis definition",
      aliases: ["Lewis acid-base definition"],
      definition: "The broadest acid–base definition: acids accept electron pairs and bases donate electron pairs, covering reactions with no proton transfer (e.g., BF₃)." },
    { term: "Arrhenius acid",
      definition: "A substance that increases H⁺ concentration in aqueous solution." },
    { term: "Arrhenius base",
      definition: "A substance that increases OH⁻ concentration in aqueous solution." },
    { term: "Arrhenius definition",
      definition: "The narrowest acid–base definition: acids produce H⁺ in water and bases produce OH⁻ in water." },
    { term: "Amphoteric",
      definition: "Capable of acting as either an acid or a base." },
    { term: "Amphiprotic",
      definition: "Capable of both donating and accepting a proton (e.g., water, HCO₃⁻)." },
    { term: "pKa",
      definition: "−log(Ka); a lower pKa indicates a stronger acid." },
    { term: "Equivalence point",
      definition: "The point in a titration at which stoichiometrically equal amounts of acid and base have reacted." },
    { term: "Half-equivalence point",
      definition: "The point in a titration at which half the analyte has been neutralized, so [HA] = [A⁻] and pH = pKa for a weak acid." },
    { term: "Titration",
      definition: "A technique in which a solution of known concentration (the titrant) is added to a solution of unknown concentration to determine the latter." },
    { term: "Solubility product",
      aliases: ["Ksp"],
      definition: "The equilibrium constant for dissolution of a sparingly soluble salt; for salts with the same ion ratio, a smaller Ksp indicates lower molar solubility." },
    { term: "Nucleophile",
      definition: "An electron-rich species that donates an electron pair to form a bond (a Lewis base)." },
    { term: "Electrophile",
      definition: "An electron-poor species that accepts an electron pair (a Lewis acid)." },
    { term: "SN1 reaction",
      definition: "Unimolecular nucleophilic substitution: the leaving group departs to form a planar carbocation, then the nucleophile attacks; it gives racemization and is favored by tertiary substrates and polar protic solvents." },
    { term: "SN2 reaction",
      definition: "Bimolecular nucleophilic substitution: the nucleophile attacks from behind in one concerted step, inverting configuration at the carbon; favored by primary substrates and polar aprotic solvents." },
    { term: "Carbocation",
      definition: "A trivalent carbon bearing a positive charge; an electrophilic intermediate stabilized by alkyl groups and resonance." },
    { term: "Anomeric carbon",
      definition: "The carbonyl carbon that becomes a new stereocenter when a monosaccharide cyclizes; its configuration defines the α versus β anomer." },
    { term: "Chiral center",
      aliases: ["stereocenter", "chiral carbon"],
      definition: "A carbon bonded to four different groups, giving rise to non-superimposable mirror-image stereoisomers." },
    { term: "Enantiomers",
      definition: "Stereoisomers that are non-superimposable mirror images of each other." },
    { term: "Diastereomers",
      definition: "Stereoisomers that are not mirror images of each other." },
    { term: "IUPAC priority",
      definition: "The hierarchy of functional groups used to choose the parent-chain suffix in naming; carboxylic acids rank highest among common groups and halides lowest." },
    { term: "Michaelis–Menten kinetics",
      aliases: ["Michaelis-Menten kinetics", "Michaelis–Menten", "Michaelis-Menten"],
      definition: "A model of enzyme kinetics in which rate = Vmax[S]/(Km + [S]); Km is the substrate concentration at half Vmax and reflects apparent substrate affinity." },
    { term: "Km",
      definition: "The Michaelis constant: the substrate concentration at which an enzyme works at half its Vmax; a lower Km indicates higher apparent substrate affinity." },
    { term: "Vmax",
      definition: "The maximum reaction velocity of an enzyme when it is saturated with substrate." },
    { term: "Lineweaver–Burk plot",
      aliases: ["Lineweaver-Burk plot"],
      definition: "A double-reciprocal plot (1/V vs 1/[S]) used to determine Km and Vmax and to distinguish competitive, noncompetitive, and uncompetitive inhibition." },
    { term: "Competitive inhibitor",
      definition: "A molecule that competes with substrate for the active site; it raises apparent Km but leaves Vmax unchanged (surmountable by high substrate concentration)." },
    { term: "Noncompetitive inhibitor",
      definition: "A molecule that binds outside the active site and lowers Vmax without changing Km." },
    { term: "Induced fit",
      definition: "A model of enzyme–substrate binding in which the enzyme's active site changes shape around the substrate to stabilize the transition state." },
    { term: "Isoelectric point",
      aliases: ["pI"],
      definition: "The pH at which a molecule carries no net charge; for amino acids it is the average of the two pKa values that bracket the neutral form." },
    { term: "Zwitterion",
      definition: "A molecule carrying both positive and negative charges but neutral overall, as amino acids at physiological pH." },
    { term: "Substrate-level phosphorylation",
      definition: "Direct transfer of a phosphate to ADP from a phosphorylated intermediate; occurs in glycolysis and the TCA cycle." },
    { term: "Oxidative phosphorylation",
      definition: "ATP synthesis driven by the proton-motive force across the inner mitochondrial membrane via ATP synthase, coupled to the electron transport chain." },
    { term: "Hardy–Weinberg equilibrium",
      aliases: ["Hardy-Weinberg equilibrium", "Hardy–Weinberg", "Hardy-Weinberg"],
      definition: "A model in which allele frequencies stay constant across generations when there is no mutation, migration, selection, genetic drift, or nonrandom mating; genotype frequencies are given by p² + 2pq + q² = 1." },
    { term: "Silent mutation",
      definition: "A DNA change that does not alter the encoded amino acid, made possible by the degeneracy of the genetic code." },
    { term: "Genetic code degeneracy",
      aliases: ["degeneracy of the genetic code", "degenerate code"],
      definition: "Multiple codons specifying the same amino acid, buffering the organism against the effects of point mutations." },
    { term: "Codon",
      definition: "A three-nucleotide mRNA sequence that specifies one amino acid or a stop signal." },
    { term: "Effective nuclear charge",
      aliases: ["Zeff"],
      definition: "The net positive charge experienced by an electron after accounting for shielding by inner electrons; it increases across a period, pulling valence electrons closer." },
    { term: "Electronegativity",
      definition: "An atom's tendency to attract shared electrons in a bond; it increases across a period and decreases down a group." },
    { term: "Ionization energy",
      definition: "The energy required to remove an electron from a gaseous atom; it increases across a period and decreases down a group." },
    { term: "Glycosidic bond",
      definition: "The covalent bond linking monosaccharides, formed between the anomeric carbon of one sugar and a hydroxyl group of another." },
    { term: "Work–kinetic energy theorem",
      aliases: ["work-kinetic energy theorem", "work-energy theorem"],
      definition: "The net work done on an object equals its change in kinetic energy (W_net = ΔKE), illustrating energy as the ability to do work." },
    { term: "Mechanical advantage",
      definition: "The ratio of output force to input force a simple machine provides (MA = F_out/F_in), equivalently the ratio of input distance to output distance." },
    { term: "Terminal velocity",
      definition: "The constant velocity a falling object reaches when the drag force equals its weight, so the net force is zero." },
    { term: "Bernoulli's equation",
      aliases: ["Bernoulli's principle", "Bernoulli equation"],
      definition: "For ideal (inviscid) fluid flow, pressure + ½ρv² + ρgh is constant along a streamline; it expresses energy conservation in fluids." },
    { term: "Viscosity",
      definition: "A fluid's internal resistance to flow; viscous forces are nonconservative and dissipate energy, so ideal-fluid assumptions ignore them." },
    { term: "Right-hand rule",
      definition: "A mnemonic for the direction of the magnetic force on a moving charge or current: the force is perpendicular to both the velocity and the magnetic field." },
    { term: "Electromagnetic radiation",
      aliases: ["EM radiation", "electromagnetic waves"],
      definition: "All EM waves travel at speed c in a vacuum (c = λf), and photon energy is E = hf, so higher frequency and shorter wavelength mean higher energy." },

    // ----- Biology & Biochemistry -----
    { term: "Hippocampus",
      definition: "A medial temporal lobe structure essential for consolidating new explicit (declarative) long-term memories." },
    { term: "Amygdala",
      definition: "An almond-shaped structure central to processing fear, emotion, and emotional memory." },
    { term: "Long-term potentiation",
      aliases: ["LTP"],
      definition: "A lasting strengthening of synapses from repeated stimulation; a cellular basis of learning and memory." },
    { term: "Neuroplasticity",
      aliases: ["plasticity"],
      definition: "The brain's ability to reorganize synaptic connections in response to experience." },
    { term: "Reuptake",
      definition: "Removal of neurotransmitter from the synaptic cleft back into the presynaptic terminal; SSRIs block serotonin reuptake to raise synaptic serotonin." },
    { term: "Action potential",
      definition: "A rapid, all-or-nothing depolarization of the neuron membrane driven by voltage-gated Na⁺ influx and terminated by K⁺ efflux." },
    { term: "Resting membrane potential",
      definition: "The voltage across a neuron membrane at rest (about −70 mV), set largely by K⁺ gradients and the Na⁺/K⁺ ATPase." },
    { term: "Two-point threshold",
      definition: "The minimum distance at which two simultaneous touch stimuli are perceived as distinct; it is inversely related to touch-receptor density." },
    { term: "Physiological zero",
      definition: "Normal skin temperature, the baseline against which temperature changes are perceived." },
    { term: "Osmosis",
      definition: "Diffusion of water across a semipermeable membrane toward the side with higher solute concentration." },
    { term: "Homeostasis",
      definition: "Maintenance of a stable internal environment through feedback mechanisms (e.g., temperature, glucose, pH)." },
    { term: "Negative feedback",
      definition: "A regulatory mechanism in which a change in a variable triggers responses that oppose the change, returning the system toward baseline." },
    { term: "Positive feedback",
      definition: "A mechanism that amplifies a change and moves the system further from baseline (e.g., the action-potential upstroke, labor contractions)." },

    // ----- Psychology & Sociology -----
    { term: "Classical conditioning",
      definition: "Learning through association: a neutral stimulus, paired with an unconditioned stimulus, becomes a conditioned stimulus that elicits a conditioned response." },
    { term: "Operant conditioning",
      definition: "Learning in which behavior is shaped by consequences: reinforcement increases a behavior and punishment decreases it." },
    { term: "Reinforcement",
      definition: "A consequence that increases the likelihood of a behavior." },
    { term: "Punishment",
      definition: "A consequence that decreases the likelihood of a behavior." },
    { term: "Working memory",
      definition: "Baddeley's limited-capacity system for actively manipulating information, with a central executive, phonological loop, visuospatial sketchpad, and episodic buffer." },
    { term: "Sensory memory",
      definition: "A very brief store of raw sensory input (iconic for vision, echoic for audition)." },
    { term: "Long-term memory",
      definition: "The relatively permanent store of information, divided into explicit (declarative) and implicit (nondeclarative) memory." },
    { term: "Explicit memory",
      aliases: ["declarative memory"],
      definition: "Conscious memory of facts (semantic) and events (episodic), dependent on the hippocampus." },
    { term: "Implicit memory",
      aliases: ["nondeclarative memory"],
      definition: "Unconscious memory such as procedural skills (basal ganglia, cerebellum) and priming." },
    { term: "Anterograde amnesia",
      definition: "Inability to form new long-term memories after an injury (e.g., hippocampal damage)." },
    { term: "Retrograde amnesia",
      definition: "Loss of memories formed before an injury." },
    { term: "Atkinson–Shiffrin model",
      aliases: ["Atkinson-Shiffrin model"],
      definition: "A memory model with sensory, short-term, and long-term stores through which information flows via attention and encoding." },
    { term: "Testing effect",
      definition: "Enhanced long-term retention from retrieval practice (testing) relative to rereading or other passive study strategies." },
    { term: "Sapir–Whorf hypothesis",
      aliases: ["Sapir-Whorf hypothesis", "Whorfian hypothesis", "linguistic relativity"],
      definition: "The claim that language influences thought, perception, and categorization." },
    { term: "Cognitive appraisal",
      aliases: ["cognitive appraisal model"],
      definition: "Lazarus's model of stress: primary appraisal evaluates whether a situation is a threat, and secondary appraisal evaluates available coping resources." },
    { term: "Ego-syntonic",
      definition: "Symptoms or traits that are consistent with a person's self-image and therefore not seen as problematic (common in personality disorders)." },
    { term: "Ego-dystonic",
      definition: "Symptoms experienced as distressing and inconsistent with one's self-image (common in anxiety disorders)." },
    { term: "Looking-glass self",
      definition: "Cooley's concept that self-concept develops from how we imagine others perceive and judge us." },
    { term: "Self-fulfilling prophecy",
      definition: "A belief or expectation that evokes behavior making the expectation come true." },
    { term: "Social stratification",
      definition: "The systematic ranking of individuals and groups in a hierarchy based on wealth, income, education, and power." },
    { term: "Social mobility",
      definition: "Movement between social positions or classes; class systems allow more mobility than caste systems." },
    { term: "Class system",
      definition: "A form of stratification based on achieved status, permitting upward or downward mobility through effort such as education or career." },
    { term: "Caste system",
      definition: "A form of stratification based on ascribed status at birth; positions are rigid and mobility is minimal." },
    { term: "Social movement",
      definition: "Tarrow's definition: collective challenges based on common purposes and social solidarities, in sustained interaction with elites, opponents, and authorities." },
    { term: "Framing",
      definition: "Constructing and articulating a message in a compelling way to win people to a cause and call them to action." },
    { term: "Manifest functions",
      definition: "The intended and recognized consequences of a social institution." },
    { term: "Latent functions",
      definition: "The unintended and unrecognized consequences of a social institution." },
    { term: "Dysfunctions",
      definition: "Consequences of a social institution that disrupt social order." },
    { term: "Cultural relativism",
      definition: "The view that a culture's practices and beliefs should be judged by its own standards rather than those of another culture." },
    { term: "Groupthink",
      definition: "Janis's concept: a group's drive for consensus suppresses dissent and critical evaluation, leading to poor decisions." },
    { term: "Resocialization",
      definition: "Replacing previous behavior patterns with new ones during a major life transition, such as leaving an institution or role." },

    // ----- CARS -----
    { term: "Deontology",
      definition: "Kant's duty-based ethics: acts are judged by their adherence to moral rules and intentions rather than by their consequences." },
    { term: "Utilitarianism",
      definition: "A consequentialist ethical theory: the best action is the one that maximizes overall utility (happiness or well-being)." },
    { term: "Doctrine of double effect",
      definition: "A principle permitting an action with a foreseeable but unintended harmful side effect if the intended effect is good and the harm is proportionate." },
  ];

  // Concise definitions for every question `topic` used in the bank. These
  // power the per-question "Key concept" chip and its hover definition.
  const TOPIC_DEFINITIONS = {
    // Biochemistry & Biology
    "Amino Acids, Peptides, and Proteins": "Amino acid chemistry, peptide bonding, and protein structure.",
    "Amino Acids and Proteins": "Amino acid ionization, peptide bonds, and protein structure and function.",
    "Protein Structure": "Primary, secondary, tertiary, and quaternary protein organization and the forces that stabilize each level.",
    "Enzymes": "Biological catalysts that lower activation energy, including active sites, specificity, and regulation.",
    "Enzymes and Enzyme Kinetics": "Enzyme function with a focus on Michaelis–Menten kinetics, Km, Vmax, and inhibition.",
    "Enzyme Kinetics": "Quantitative study of enzyme reaction rates: Km, Vmax, and the effects of inhibitors.",
    "Enzymes and Metabolic Regulation": "How committed, allosterically regulated enzymes act as control points in metabolic pathways.",
    "Metabolism: Glycolysis, TCA Cycle, and Oxidative Phosphorylation": "The central energy pathways: glucose breakdown, the citric acid cycle, and ATP production via the electron transport chain.",
    "Bioenergetics and Cellular Respiration": "Energy flow in cells, including ATP, redox reactions, and aerobic respiration.",
    "Carbohydrates and Glycobiology": "Structure and biological roles of carbohydrates.",
    "Carbohydrates and Lipids": "Structure, properties, and biological roles of carbohydrates and lipids.",
    "Lipids and Biological Membranes": "Lipid structure and the assembly and function of biological membranes.",
    "Transcription and Translation": "Gene expression: DNA-to-RNA transcription and RNA-to-protein translation.",
    "DNA Structure and Replication": "The double-helix structure of DNA and its semiconservative replication.",
    "Nucleic Acids and Gene Expression": "DNA and RNA structure and the regulation of gene expression.",
    "Genetics and Evolution": "Mendelian genetics, heredity, and the mechanisms of evolution.",
    "Molecular Genetics and Mutations": "The molecular basis of genes, including mutation types and their consequences.",
    "Molecular Biology Techniques": "Laboratory methods such as blotting, PCR, and sequencing used to study nucleic acids and proteins.",
    "The Cell": "Cell structure, organelles, and basic cellular processes.",
    "Reproduction": "Cellular and organismal reproduction, including mitosis and meiosis.",
    "Embryogenesis and Development": "Stages of embryonic development and the processes of determination and differentiation.",
    "The Nervous System": "Neuron structure and signaling, and the organization of the nervous system.",
    "The Endocrine System": "Hormones, endocrine glands, and their regulation of physiology.",
    "Endocrine System": "Hormonal signaling and the glands that regulate the body.",
    "Nervous and Endocrine Systems": "Integration of neural and hormonal control of the body.",
    "The Respiratory System": "Anatomy and physiology of breathing and gas exchange.",
    "The Cardiovascular System": "The heart, blood vessels, and circulation.",
    "The Immune System": "Innate and adaptive immune defenses.",
    "The Digestive System": "Mechanical and chemical digestion and nutrient absorption.",
    "The Musculoskeletal System": "Muscle and bone structure, function, and movement.",
    "Muscle Tissue and Physiology": "Muscle cell types, contraction mechanisms, and their regulation.",
    "Homeostasis": "Maintenance of a stable internal environment through feedback control.",

    // General Chemistry
    "Atomic Structure": "Subatomic particles, atomic number, isotopes, and electron configuration.",
    "The Periodic Table": "Organization of the elements and the information it encodes.",
    "Periodic Table Trends": "Periodic trends in atomic radius, ionization energy, electronegativity, and electron affinity.",
    "Bonding and Chemical Interactions": "Ionic, covalent, and intermolecular interactions.",
    "Compounds and Stoichiometry": "Chemical formulas, moles, and quantitative relationships in reactions.",
    "Chemical Kinetics": "Reaction rates, rate laws, and the factors that affect reaction speed.",
    "Equilibrium": "Dynamic balance between forward and reverse reactions.",
    "Chemical Equilibrium": "Equilibrium constants, reaction quotients, and Le Chatelier's principle.",
    "Thermochemistry": "Heat changes in chemical processes, including ΔH and calorimetry.",
    "Thermodynamics": "Energy, enthalpy, entropy, and Gibbs free energy in chemical and physical processes.",
    "Acids and Bases": "Acid–base definitions, pH, pKa, buffers, and titrations.",
    "Oxidation-Reduction Reactions": "Electron-transfer reactions and oxidation states.",
    "Electrochemistry": "Redox reactions in galvanic and electrolytic cells.",
    "The Gas Phase": "Ideal and real gas behavior, PV = nRT.",
    "Solutions": "Concentration, solubility, and colligative properties.",

    // Organic Chemistry
    "Stereochemistry and Isomers": "Spatial arrangement of atoms and the relationships between isomers.",
    "Stereochemistry": "Three-dimensional molecular arrangement and chirality.",
    "Stereochemistry and Isomerism": "Isomer types, including constitutional, conformational, and configurational isomers.",
    "Substitution and Elimination Reactions": "SN1/SN2 substitution and E1/E2 elimination mechanisms.",
    "Carbonyl Chemistry": "Reactions of aldehydes, ketones, and carboxylic acid derivatives.",
    "Functional Groups and Nomenclature": "Identifying functional groups and naming organic compounds.",
    "Nomenclature and Functional Groups": "IUPAC naming and functional-group recognition.",
    "Acids and Bases in Organic Chemistry": "Organic acid–base reactivity and pKa in organic contexts.",
    "Organic Reaction Mechanisms": "Step-by-step pathways of organic reactions.",
    "Laboratory Techniques and Spectroscopy": "Purification and separation methods and structural determination.",
    "Spectroscopy and Structure Determination": "IR, NMR, and mass spectrometry for identifying molecular structure.",

    // Physics
    "Kinematics and Dynamics": "Motion and the forces that cause it, including Newton's laws.",
    "Work and Energy": "Work, kinetic and potential energy, and conservation of energy.",
    "Fluids": "Pressure, buoyancy, and fluid flow.",
    "Circuits": "Current, voltage, resistance, and circuit analysis.",
    "Electrostatics and Magnetism": "Electric charge, fields, and magnetic forces.",
    "Electromagnetism": "Electric and magnetic fields and their interactions.",
    "Waves and Sound": "Wave properties and sound phenomena.",
    "Light and Optics": "Electromagnetic radiation, lenses, and mirrors.",

    // Psychology & Sociology
    "Sensation and Perception": "Sensory processing and the interpretation of stimuli.",
    "Learning": "Classical and operant conditioning and observational learning.",
    "Learning and Behavior": "Behavioral theories of how learning occurs.",
    "Cognition and Language": "Thinking, problem solving, memory, and language.",
    "Memory": "Encoding, storage, and retrieval of information.",
    "Consciousness and Sleep": "States of consciousness and sleep stages and disorders.",
    "Biological Bases of Behavior": "Neural and endocrine underpinnings of behavior.",
    "Biopsychosocial Model": "The interplay of biological, psychological, and social factors in health and behavior.",
    "Research Methods and Statistics": "Experimental design, measurement, and statistical inference.",
    "Personality": "Theories and assessment of personality.",
    "Self and Identity": "Self-concept, identity formation, and social identity.",
    "Psychological Disorders": "Classification and characteristics of mental disorders.",
    "Developmental Psychology": "Cognitive, social, and physical development across the lifespan.",
    "Motivation and Emotion": "Drives that direct behavior and the experience of emotion.",
    "Stress and Coping": "Stress responses and coping strategies.",
    "Social Psychology": "How individuals influence and are influenced by others.",
    "Attribution Theory": "How people explain the causes of behavior and events.",
    "Social Interaction and Groups": "Dynamics of groups, norms, and social interaction.",
    "Social Structure and Institutions": "Organized patterns of social relationships and institutions.",
    "Social Stratification and Inequality": "Hierarchical ranking and unequal distribution of resources.",
    "Social Stratification": "Ranking of individuals and groups into a social hierarchy.",
    "Culture and Socialization": "Transmission of culture and the process of socialization.",
    "Demography and Urbanization": "Population structure, change, and urban growth.",
    "Social Change and Globalization": "How societies change and global interconnectedness.",

    // CARS
    "Literature and Literary Criticism": "Analysis of literary texts and critical approaches.",
    "Philosophy and Ethics": "Philosophical arguments and ethical frameworks.",
    "Art History and Aesthetics": "Artistic movements and theories of aesthetic value.",
    "History": "Interpreting historical narratives and causation.",
    "Cultural Studies and Religion": "Culture and religious systems in society.",
    "Philosophy of Science and Technology": "Epistemology of science and the role of technology.",
    "Main Idea and Structure": "Identifying a passage's central claim and organization.",
    "Tone and Rhetoric": "Authorial attitude and rhetorical strategies.",
    "Detail and Evidence": "Locating and interpreting specific passage details.",
    "Strengthen-Weaken Reasoning": "Evaluating how evidence strengthens or weakens an argument.",
    "Political Science and Government": "Political systems, power, and governance.",
    "Sociology and Anthropology": "Social structures, culture, and human societies.",
    "Economics and Business": "Economic principles and business behavior.",
    "Psychology and Social Behavior": "Psychological principles applied to social behavior.",
  };

  // ---------------------------------------------------------------------
  // Matching + escaping
  // ---------------------------------------------------------------------
  const entries = [];
  GLOSSARY.forEach((g) => {
    const names = [g.term].concat(g.aliases || []);
    names.forEach((name) => entries.push({ name: String(name), entry: g }));
  });
  // Longest-first so more specific terms ("Brønsted–Lowry acid") win over
  // shorter substrings before overlapping matches are dropped.
  entries.sort((a, b) => b.name.length - a.name.length);

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "\u0026amp;")
      .replace(/</g, "\u0026lt;")
      .replace(/>/g, "\u0026gt;")
      .replace(/"/g, "\u0026quot;")
      .replace(/'/g, "\u0026#39;");
  }

  function isWordChar(ch) {
    return !!ch && /[A-Za-z0-9]/.test(ch);
  }

  // Find every glossary match in a plain-text string: [{start, end, entry}].
  function findMatches(src) {
    const lower = src.toLowerCase();
    const matches = [];
    for (const e of entries) {
      const needle = e.name.toLowerCase();
      if (!needle) continue;
      let from = 0;
      while (from < src.length) {
        const idx = lower.indexOf(needle, from);
        if (idx === -1) break;
        const before = src[idx - 1];
        const after = src[idx + needle.length];
        if (!isWordChar(before) && !isWordChar(after)) {
          matches.push({ start: idx, end: idx + needle.length, entry: e.entry });
          from = idx + needle.length;
        } else {
          from = idx + 1;
        }
      }
    }
    return matches;
  }

  // Escape text and wrap recognized concepts in hoverable spans.
  // opts.terms — optional array of canonical terms; when set, only those
  //              concepts are highlighted.
  // opts.limit — optional cap on the number of DISTINCT concepts highlighted.
  function linkify(text, opts) {
    const src = String(text == null ? "" : text);
    if (!src) return "";

    let matches = findMatches(src);
    if (opts && Array.isArray(opts.terms)) {
      const allowed = new Set(opts.terms);
      matches = matches.filter((m) => allowed.has(m.entry.term));
    }

    if (!matches.length) return escapeHtml(src);

    // Longest matches first; drop overlaps; then clamp distinct concepts.
    matches.sort((a, b) => (b.end - b.start) - (a.end - a.start) || a.start - b.start);
    const accepted = [];
    for (const m of matches) {
      if (accepted.some((a) => m.start < a.end && m.end > a.start)) continue;
      accepted.push(m);
    }
    accepted.sort((a, b) => a.start - b.start);

    let final = accepted;
    if (opts && typeof opts.limit === "number" && opts.limit > 0) {
      const chosen = [];
      for (const m of accepted) {
        if (chosen.length >= opts.limit) break;
        if (chosen.indexOf(m.entry.term) === -1) chosen.push(m.entry.term);
      }
      final = accepted.filter((m) => chosen.indexOf(m.entry.term) !== -1);
    }

    let out = "";
    let cursor = 0;
    for (const m of final) {
      out += escapeHtml(src.slice(cursor, m.start));
      const dataTerm = escapeHtml(m.entry.term);
      out += '<span class="concept" tabindex="0" data-term="' + dataTerm + '">' +
        escapeHtml(src.slice(m.start, m.end)) + '</span>';
      cursor = m.end;
    }
    out += escapeHtml(src.slice(cursor));
    return out;
  }

  // The question's core concepts: its `topic` plus the technical glossary
  // terms that matter most to this question. Stem hits rank before
  // explanation hits; longer terms rank first; capped at `limit`.
  function keyConcepts(q, limit) {
    const topic = q && q.topic ? String(q.topic) : null;
    const cap = limit || 3;
    const ranked = [];
    const seen = new Set();
    function collect(text, weight) {
      if (!text) return;
      findMatches(String(text)).forEach((m) => {
        if (seen.has(m.entry.term)) return;
        seen.add(m.entry.term);
        ranked.push({ term: m.entry.term, weight: weight, len: m.entry.term.length });
      });
    }
    collect(q && q.question, 0);
    collect(q && q.explanation, 1);
    ranked.sort((a, b) => a.weight - b.weight || b.len - a.len);
    return { topic: topic, terms: ranked.slice(0, cap).map((t) => t.term) };
  }

  // ---------------------------------------------------------------------
  // Floating tooltip
  // ---------------------------------------------------------------------
  let tooltipEl = null;
  let currentConcept = null;
  let hideTimer = null;

  function getTooltip() {
    if (tooltipEl) return tooltipEl;
    tooltipEl = document.createElement("div");
    tooltipEl.id = "concept-tooltip";
    tooltipEl.setAttribute("role", "tooltip");
    tooltipEl.hidden = true;
    document.body.appendChild(tooltipEl);
    return tooltipEl;
  }

  function definitionFor(term) {
    for (const g of GLOSSARY) if (g.term === term) return g.definition;
    if (TOPIC_DEFINITIONS[term]) return TOPIC_DEFINITIONS[term];
    if (term) {
      if (typeof console !== "undefined" && console.warn) {
        console.warn("[glossary] missing definition for:", term);
      }
      return "A key MCAT concept under " + term + ".";
    }
    return "";
  }

  // Highlighted, hoverable pill for a question's primary key concept.
  // Pass `href` to render it as a link (e.g. "practice this deck") instead of a
  // non-interactive span; it keeps the same .concept tooltip/hover behavior.
  function conceptChip(term, href) {
    if (!term) return "";
    const t = String(term);
    const inner = '<span class="concept-chip-label">Key concept</span>' + escapeHtml(t);
    if (href) {
      return '<a class="concept concept-chip concept-chip-link" href="' + escapeHtml(href) + '" data-term="' + escapeHtml(t) + '">' + inner + '</a>';
    }
    return '<span class="concept concept-chip" tabindex="0" data-term="' + escapeHtml(t) + '">' + inner + '</span>';
  }

  // Render a question's figure as a `.figure` block plus an optional caption.
  // `q.figure` is trusted SVG/HTML produced by our own renderer (figure_lib.py),
  // so it is inserted verbatim; only the caption is escaped.
  function figureHTML(q) {
    if (!q || !q.figure) return "";
    let html = '<div class="figure">' + q.figure + '</div>';
    if (q.figure_caption) {
      html += '<div class="figure-caption">' + escapeHtml(q.figure_caption) + '</div>';
    }
    return html;
  }

  function coordsOf(e) {
    if (e && typeof e.clientX === "number") return { x: e.clientX, y: e.clientY };
    const t = e && e.touches && e.touches[0];
    if (t) return { x: t.clientX, y: t.clientY };
    const r = e && e.target && e.target.getBoundingClientRect;
    if (r) { const b = e.target.getBoundingClientRect(); return { x: b.left, y: b.bottom }; }
    return { x: 0, y: 0 };
  }

  function show(span, e) {
    const term = span.dataset.term;
    const def = definitionFor(term);
    if (!def) return;
    const tip = getTooltip();
    tip.innerHTML =
      '<strong class="concept-tooltip-term">' + escapeHtml(term) + '</strong>' +
      '<span class="concept-tooltip-def">' + escapeHtml(def) + '</span>';
    tip.hidden = false;
    position(coordsOf(e));
  }

  function position(c) {
    if (!tooltipEl || tooltipEl.hidden) return;
    const pad = 12;
    const tipW = tooltipEl.offsetWidth;
    const tipH = tooltipEl.offsetHeight;
    let x = c.x + 14;
    let y = c.y + 16;
    if (x + tipW + pad > window.innerWidth) x = c.x - tipW - 14;
    if (y + tipH + pad > window.innerHeight) y = c.y - tipH - 16;
    x = Math.max(pad, Math.min(x, window.innerWidth - tipW - pad));
    y = Math.max(pad, Math.min(y, window.innerHeight - tipH - pad));
    tooltipEl.style.left = x + "px";
    tooltipEl.style.top = y + "px";
  }

  function hide() {
    if (tooltipEl) {
      tooltipEl.hidden = true;
      tooltipEl.innerHTML = "";
    }
    currentConcept = null;
  }

  function findConcept(target) {
    return target && target.closest ? target.closest(".concept") : null;
  }

  function initTooltips(scope) {
    const root = scope || document;

    // Mouse / pen hover (pointer events; touch is handled separately below).
    root.addEventListener("pointerover", function (e) {
      if (e.pointerType === "touch") return;
      const span = findConcept(e.target);
      if (!span) return;
      currentConcept = span;
      clearTimeout(hideTimer);
      show(span, e);
    });
    root.addEventListener("pointermove", function (e) {
      if (e.pointerType === "touch") return;
      if (currentConcept && tooltipEl && !tooltipEl.hidden) position(coordsOf(e));
    });
    root.addEventListener("pointerout", function (e) {
      if (e.pointerType === "touch") return;
      const span = findConcept(e.target);
      if (span && span === currentConcept) {
        hideTimer = setTimeout(hide, 120);
      }
    });

    // Keyboard accessibility.
    root.addEventListener("focusin", function (e) {
      const span = findConcept(e.target);
      if (!span) return;
      currentConcept = span;
      clearTimeout(hideTimer);
      show(span, e);
    });
    root.addEventListener("focusout", function (e) {
      const span = findConcept(e.target);
      if (span && span === currentConcept) hide();
    });

    // Touch: tap toggles the tooltip on/off.
    root.addEventListener("touchstart", function (e) {
      const span = findConcept(e.target);
      if (!span) return;
      if (tooltipEl && !tooltipEl.hidden && currentConcept === span) {
        hide();
        return;
      }
      currentConcept = span;
      show(span, e);
    }, { passive: true });

    // Dismiss a touch-opened tooltip when tapping elsewhere.
    root.addEventListener("touchstart", function (e) {
      if (!findConcept(e.target) && tooltipEl && !tooltipEl.hidden) hide();
    }, { passive: true });
  }

  window.Glossary = {
    GLOSSARY: GLOSSARY,
    TOPIC_DEFINITIONS: TOPIC_DEFINITIONS,
    linkify: linkify,
    keyConcepts: keyConcepts,
    conceptChip: conceptChip,
    figureHTML: figureHTML,
    initTooltips: initTooltips,
  };

  // Auto-initialize the delegated tooltip once the document is ready.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { initTooltips(document); });
  } else {
    initTooltips(document);
  }
})();
