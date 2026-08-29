(function () {
  renderNav("flashcards");
  const root = document.getElementById("page-root");

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : s;
    return d.innerHTML;
  }

  // Flashcard decks must not be smaller than this. The question bank carries
  // ~100 fine-grained topics (10-20 questions each), which made for dozens of
  // stubby decks; TOPIC_CONSOLIDATION rolls them up into a handful of broad
  // decks, and enforceMinDeck() is the backstop for anything not in the map.
  const MIN_DECK = 30;

  const TOPIC_CONSOLIDATION = {
    // Biological & Biochemical Foundations
    "Amino Acids, Peptides, and Proteins": "Biochemistry: Proteins & Enzymes",
    "Amino Acids and Proteins": "Biochemistry: Proteins & Enzymes",
    "Protein Structure": "Biochemistry: Proteins & Enzymes",
    "Enzymes": "Biochemistry: Proteins & Enzymes",
    "Enzymes and Enzyme Kinetics": "Biochemistry: Proteins & Enzymes",
    "Enzyme Kinetics": "Biochemistry: Proteins & Enzymes",
    "Enzymes and Metabolic Regulation": "Biochemistry: Proteins & Enzymes",
    "Metabolism: Glycolysis, TCA Cycle, and Oxidative Phosphorylation": "Biochemistry: Metabolism & Biomolecules",
    "Bioenergetics and Cellular Respiration": "Biochemistry: Metabolism & Biomolecules",
    "Carbohydrates and Glycobiology": "Biochemistry: Metabolism & Biomolecules",
    "Carbohydrates and Lipids": "Biochemistry: Metabolism & Biomolecules",
    "Lipids and Biological Membranes": "Biochemistry: Metabolism & Biomolecules",
    "Transcription and Translation": "Molecular Biology & Genetics",
    "DNA Structure and Replication": "Molecular Biology & Genetics",
    "Nucleic Acids and Gene Expression": "Molecular Biology & Genetics",
    "Genetics and Evolution": "Molecular Biology & Genetics",
    "Molecular Genetics and Mutations": "Molecular Biology & Genetics",
    "Molecular Biology Techniques": "Molecular Biology & Genetics",
    "The Cell": "Cell Biology & Development",
    "Reproduction": "Cell Biology & Development",
    "Embryogenesis and Development": "Cell Biology & Development",
    "The Nervous System": "Physiology: Nervous & Endocrine Systems",
    "The Endocrine System": "Physiology: Nervous & Endocrine Systems",
    "Endocrine System": "Physiology: Nervous & Endocrine Systems",
    "Nervous and Endocrine Systems": "Physiology: Nervous & Endocrine Systems",
    "The Respiratory System": "Physiology: Organ Systems",
    "The Cardiovascular System": "Physiology: Organ Systems",
    "The Immune System": "Physiology: Organ Systems",
    "The Digestive System": "Physiology: Organ Systems",
    "The Musculoskeletal System": "Physiology: Organ Systems",
    "Muscle Tissue and Physiology": "Physiology: Organ Systems",
    "Homeostasis": "Physiology: Organ Systems",
    // Chemical & Physical Foundations
    "Atomic Structure": "General Chemistry: Atomic Structure & Bonding",
    "The Periodic Table": "General Chemistry: Atomic Structure & Bonding",
    "Periodic Table Trends": "General Chemistry: Atomic Structure & Bonding",
    "Bonding and Chemical Interactions": "General Chemistry: Atomic Structure & Bonding",
    "Compounds and Stoichiometry": "General Chemistry: Atomic Structure & Bonding",
    "Chemical Kinetics": "General Chemistry: Thermo, Kinetics & Equilibrium",
    "Equilibrium": "General Chemistry: Thermo, Kinetics & Equilibrium",
    "Chemical Equilibrium": "General Chemistry: Thermo, Kinetics & Equilibrium",
    "Thermochemistry": "General Chemistry: Thermo, Kinetics & Equilibrium",
    "Thermodynamics": "General Chemistry: Thermo, Kinetics & Equilibrium",
    "Acids and Bases": "General Chemistry: Acids/Bases, Redox & Solutions",
    "Oxidation-Reduction Reactions": "General Chemistry: Acids/Bases, Redox & Solutions",
    "Electrochemistry": "General Chemistry: Acids/Bases, Redox & Solutions",
    "The Gas Phase": "General Chemistry: Acids/Bases, Redox & Solutions",
    "Solutions": "General Chemistry: Acids/Bases, Redox & Solutions",
    "Stereochemistry and Isomers": "Organic Chemistry",
    "Stereochemistry": "Organic Chemistry",
    "Stereochemistry and Isomerism": "Organic Chemistry",
    "Substitution and Elimination Reactions": "Organic Chemistry",
    "Carbonyl Chemistry": "Organic Chemistry",
    "Functional Groups and Nomenclature": "Organic Chemistry",
    "Nomenclature and Functional Groups": "Organic Chemistry",
    "Acids and Bases in Organic Chemistry": "Organic Chemistry",
    "Organic Reaction Mechanisms": "Organic Chemistry",
    "Laboratory Techniques and Spectroscopy": "Organic Chemistry",
    "Spectroscopy and Structure Determination": "Organic Chemistry",
    "Kinematics and Dynamics": "Physics: Mechanics & Fluids",
    "Work and Energy": "Physics: Mechanics & Fluids",
    "Fluids": "Physics: Mechanics & Fluids",
    "Circuits": "Physics: Electromagnetism, Waves & Optics",
    "Electrostatics and Magnetism": "Physics: Electromagnetism, Waves & Optics",
    "Electromagnetism": "Physics: Electromagnetism, Waves & Optics",
    "Waves and Sound": "Physics: Electromagnetism, Waves & Optics",
    "Light and Optics": "Physics: Electromagnetism, Waves & Optics",
    // Psychological, Social, & Biological Foundations
    "Sensation and Perception": "Psych: Cognition, Memory & Biological Bases",
    "Learning": "Psych: Cognition, Memory & Biological Bases",
    "Learning and Behavior": "Psych: Cognition, Memory & Biological Bases",
    "Cognition and Language": "Psych: Cognition, Memory & Biological Bases",
    "Memory": "Psych: Cognition, Memory & Biological Bases",
    "Consciousness and Sleep": "Psych: Cognition, Memory & Biological Bases",
    "Biological Bases of Behavior": "Psych: Cognition, Memory & Biological Bases",
    "Biopsychosocial Model": "Psych: Cognition, Memory & Biological Bases",
    "Research Methods and Statistics": "Psych: Cognition, Memory & Biological Bases",
    "Personality": "Psych: Personality, Development & Disorders",
    "Self and Identity": "Psych: Personality, Development & Disorders",
    "Psychological Disorders": "Psych: Personality, Development & Disorders",
    "Developmental Psychology": "Psych: Personality, Development & Disorders",
    "Motivation and Emotion": "Psych: Personality, Development & Disorders",
    "Stress and Coping": "Psych: Personality, Development & Disorders",
    "Social Psychology": "Sociology & Social Psychology",
    "Attribution Theory": "Sociology & Social Psychology",
    "Social Interaction and Groups": "Sociology & Social Psychology",
    "Social Structure and Institutions": "Sociology & Social Psychology",
    "Social Stratification and Inequality": "Sociology & Social Psychology",
    "Social Stratification": "Sociology & Social Psychology",
    "Culture and Socialization": "Sociology & Social Psychology",
    "Demography and Urbanization": "Sociology & Social Psychology",
    "Social Change and Globalization": "Sociology & Social Psychology",
    // Critical Analysis and Reasoning Skills
    "Literature and Literary Criticism": "CARS: Humanities",
    "Philosophy and Ethics": "CARS: Humanities",
    "Art History and Aesthetics": "CARS: Humanities",
    "History": "CARS: Humanities",
    "Cultural Studies and Religion": "CARS: Humanities",
    "Philosophy of Science and Technology": "CARS: Humanities",
    "Main Idea and Structure": "CARS: Humanities",
    "Tone and Rhetoric": "CARS: Humanities",
    "Detail and Evidence": "CARS: Humanities",
    "Strengthen-Weaken Reasoning": "CARS: Humanities",
    "Political Science and Government": "CARS: Social Sciences",
    "Sociology and Anthropology": "CARS: Social Sciences",
    "Economics and Business": "CARS: Social Sciences",
    "Psychology and Social Behavior": "CARS: Social Sciences",
  };

  const SECTION_DECK = {
    "Biological & Biochemical Foundations": "Bio/Biochem review",
    "Chemical & Physical Foundations": "Chem/Phys review",
    "Psychological, Social, & Biological Foundations": "Psych/Soc review",
    "Critical Analysis and Reasoning Skills": "CARS review",
  };

  function consolidatedTopic(q) {
    const raw = q.topic || q.section || "General review";
    return TOPIC_CONSOLIDATION[raw] || raw;
  }

  // Backstop for any topic not covered by TOPIC_CONSOLIDATION: fold every
  // sub-threshold deck into its dominant section's review deck, then fold any
  // still-short deck into the largest remaining deck, so nothing ships < MIN_DECK
  // (unless the whole bank has fewer than MIN_DECK questions).
  function enforceMinDeck(byTopic) {
    const sectionOf = (qs) => {
      const c = {};
      qs.forEach((q) => { const s = q.section || ""; c[s] = (c[s] || 0) + 1; });
      const top = Object.keys(c).sort((a, b) => c[b] - c[a])[0] || "";
      return SECTION_DECK[top] || "Mixed review";
    };
    Object.keys(byTopic).forEach((t) => {
      if (byTopic[t].length >= MIN_DECK) return;
      const target = sectionOf(byTopic[t]);
      if (target === t) return;
      byTopic[target] = (byTopic[target] || []).concat(byTopic[t]);
      delete byTopic[t];
    });
    let guard = 0;
    while (guard++ < 50) {
      const keys = Object.keys(byTopic);
      if (keys.length <= 1) break;
      const small = keys.filter((k) => byTopic[k].length < MIN_DECK);
      if (!small.length) break;
      const largest = keys.sort((a, b) => byTopic[b].length - byTopic[a].length)[0];
      small.forEach((k) => {
        if (k === largest) return;
        byTopic[largest] = byTopic[largest].concat(byTopic[k]);
        delete byTopic[k];
      });
    }
    return byTopic;
  }

  function topicDecks() {
    const byTopic = {};
    Object.values(Data.allQuestions).forEach((q) => {
      const t = consolidatedTopic(q);
      (byTopic[t] = byTopic[t] || []).push(q);
    });
    enforceMinDeck(byTopic);
    return Object.entries(byTopic)
      .map(([topic, group]) => {
        const seen = {}, questions = [];
        group.forEach((q) => { if (!seen[q.id]) { seen[q.id] = 1; questions.push(q); } });
        return { id: `topic:${topic}`, title: topic, questions };
      })
      .sort((a, b) => a.title.localeCompare(b.title));
  }

  function missedDeck(store) {
    const qs = Object.entries(store.cards)
      .filter(([, c]) => c.lastCorrect === false)
      .map(([id]) => Data.allQuestions[id]).filter(Boolean);
    return { id: "missed", title: "Missed questions", questions: qs, auto: true };
  }

  function dueCount(store, questions) {
    const now = Date.now();
    return questions.filter((q) => { const c = store.cards[q.id]; return c && c.due && c.due <= now; }).length;
  }

  const params = new URLSearchParams(location.search);
  let store = Store.load();
  const decks = [missedDeck(store), ...topicDecks()].filter((d) => d.questions.length);

  let activeDeckId = params.get("deck") || (decks.find((d) => dueCount(store, d.questions) > 0) || decks[0] || {}).id;
  let activeDeck = decks.find((d) => d.id === activeDeckId) || decks[0];
  let idx = 0;
  let revealed = false;
  let session = { seen: 0, good: 0, hard: 0, again: 0, startedAt: Date.now() };

  function renderShell() {
    root.innerHTML = `
      <div class="page-head"><h2 style="margin:0">Flashcards</h2></div>
      <div class="panel">
        <div class="flash-grid" id="flash-grid"></div>
      </div>
    `;
    renderGrid();
  }

  function renderGrid() {
    const grid = document.getElementById("flash-grid");
    if (!activeDeck) {
      grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">No flashcards yet — answer a few practice questions first.</div>`;
      return;
    }
    grid.innerHTML = `
      <div class="deck-rail">
        <div class="k" style="margin-bottom:14px">Decks</div>
        ${decks.map((d) => `
          <div class="deck-item ${d.id === activeDeck.id ? "active" : ""}" data-id="${d.id}">
            <div class="row-title">${d.title}</div>
            <div class="row-sub">${dueCount(store, d.questions)} due · ${d.questions.length} card${d.questions.length === 1 ? "" : "s"}</div>
          </div>`).join("")}
      </div>
      <div class="flash-main" id="flash-main"></div>
      <div class="flash-side" id="flash-side"></div>
    `;
    grid.querySelectorAll(".deck-item").forEach((el) => {
      el.addEventListener("click", () => {
        activeDeck = decks.find((d) => d.id === el.dataset.id);
        idx = 0; revealed = false;
        session = { seen: 0, good: 0, hard: 0, again: 0, startedAt: Date.now() };
        renderGrid();
      });
    });
    renderCard();
    renderSide();
  }

  function renderCard() {
    const main = document.getElementById("flash-main");
    if (idx >= activeDeck.questions.length) {
      main.innerHTML = `<div class="empty-state">Deck complete for now.</div>`;
      return;
    }
    const q = activeDeck.questions[idx];
    const letters = ["A", "B", "C", "D"];
    main.innerHTML = `
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px">
        <div style="font-family:var(--font-heading);font-weight:600;font-size:14px">${activeDeck.title}</div>
        <div class="text-muted" style="font-size:12px">Card ${idx + 1} of ${activeDeck.questions.length}</div>
        <div class="bar" style="flex:1"><span style="width:${(idx / activeDeck.questions.length) * 100}%"></span></div>
        <span class="tag tag-neutral">Spaced repetition</span>
      </div>
      <div class="flash-card">
        <div class="k">Front</div>
        <p style="font-family:var(--font-heading);font-size:22px;line-height:1.3;font-weight:600;margin:10px 0 0">${escapeHtml(q.question)}</p>
        <div id="back-slot" style="margin-top:auto"></div>
      </div>
      <div id="grade-slot"></div>
    `;
    const backSlot = document.getElementById("back-slot");
    if (!revealed) {
      backSlot.innerHTML = `<button class="btn btn-primary" id="reveal-btn" style="margin-top:24px">Show answer</button>`;
      document.getElementById("reveal-btn").addEventListener("click", () => { revealed = true; renderCard(); });
    } else {
      backSlot.innerHTML = `
        <hr class="hr" style="margin:28px 0">
        <div class="k">Back</div>
        <p style="font-size:16px;line-height:1.7;margin:10px 0 0;opacity:.9"><strong>${letters[q.correct]}.</strong> ${escapeHtml(q.options[q.correct])}</p>
        <p style="font-size:14px;line-height:1.6;margin-top:10px;opacity:.8">${escapeHtml(q.explanation)}</p>
        <div style="display:flex;gap:6px;margin-top:20px">
          ${q.topic ? `<span class="tag tag-accent">${q.topic}</span>` : ""}
          <span class="tag tag-neutral">${q.section ? q.section.replace(" Foundations", "") : ""}</span>
        </div>
      `;
      renderGradeRow(q.id);
    }
  }

  function renderGradeRow(qid) {
    const slot = document.getElementById("grade-slot");
    slot.innerHTML = `
      <div class="k" style="margin-top:24px">How well did you know it?</div>
      <div class="review-row" style="margin-top:10px">
        <button class="review-btn review-again" data-key="again">Again</button>
        <button class="review-btn review-hard" data-key="hard">Hard</button>
        <button class="review-btn review-good" data-key="good">Good</button>
        <button class="review-btn review-easy" data-key="easy">Easy</button>
      </div>
    `;
    slot.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => {
        const key = btn.dataset.key;
        Store.applyGrade(qid, key);
        store = Store.load();
        session.seen += 1;
        if (key === "again") session.again += 1;
        else if (key === "hard") session.hard += 1;
        else session.good += 1;
        idx += 1; revealed = false;
        renderCard();
        renderSide();
        renderGridCounts();
      });
    });
  }

  function renderGridCounts() {
    document.querySelectorAll(".deck-item").forEach((el) => {
      const d = decks.find((x) => x.id === el.dataset.id);
      if (!d) return;
      el.querySelector(".row-sub").textContent = `${dueCount(store, d.questions)} due · ${d.questions.length} card${d.questions.length === 1 ? "" : "s"}`;
    });
  }

  function upcomingReviews() {
    const now = Date.now();
    const days = [];
    for (let i = 0; i < 7; i++) {
      const start = now + i * 86400000;
      const end = start + 86400000;
      const count = Object.values(store.cards).filter((c) => c.due && c.due >= start && c.due < end).length;
      days.push(count);
    }
    return days;
  }

  function renderSide() {
    const side = document.getElementById("flash-side");
    const mins = Math.round((Date.now() - session.startedAt) / 60000);
    const up = upcomingReviews();
    const maxUp = Math.max(1, ...up);
    side.innerHTML = `
      <div class="k">This session</div>
      <div style="display:flex;align-items:flex-end;gap:8px;margin-top:8px">
        <div class="num" style="font-size:34px">${session.seen}</div>
        <div class="text-muted" style="font-size:12px;padding-bottom:6px">/ ${activeDeck.questions.length} cards</div>
      </div>
      <div class="row-list" style="margin-top:16px;border-top:2px solid var(--color-divider)">
        <div class="kv-row"><span>Good or easy</span><strong>${session.good}</strong></div>
        <div class="kv-row"><span>Hard</span><strong>${session.hard}</strong></div>
        <div class="kv-row"><span>Again</span><strong>${session.again}</strong></div>
        <div class="kv-row"><span>Time</span><strong>${mins} min</strong></div>
      </div>
      ${activeDeck.auto ? `
        <div class="callout" style="margin-top:20px">
          <div class="k">Auto-generated</div>
          <p>Built from questions you've gotten wrong in practice — reviewing this deck helps most.</p>
        </div>` : ""}
      <div class="k" style="margin-top:24px">Upcoming reviews</div>
      <div class="chart-bars" style="height:60px;margin-top:10px">
        ${up.map((n, i) => `<div style="height:${Math.max(6, (n / maxUp) * 100)}%" class="${i === 0 ? "today" : ""}" title="${n} due"></div>`).join("")}
      </div>
      <div style="display:flex;justify-content:space-between;font-size:10px;margin-top:6px" class="text-muted"><span>Today</span><span>+6 d</span></div>
    `;
  }

  renderShell();
})();
