const root = document.getElementById("quiz-root");
const progressLabel = document.getElementById("progress-label");
const STORE_KEY = "mycat_state_v2";
const DAY_MS = 24 * 60 * 60 * 1000;
const MIN_EASE = 1.3;

let activeDeck = null;
let current = 0;
let sessionCorrect = 0;
let answered = false;

// Combine hand-written decks with the full-length generated decks.
const ALL_DECKS = (typeof DECKS !== "undefined" ? DECKS : []).concat(
  typeof FULL_DECKS !== "undefined" ? FULL_DECKS : [],
  typeof HARD_DECKS !== "undefined" ? HARD_DECKS : []
);

ALL_DECKS.forEach((deck) => {
  deck.questions.forEach((q, i) => {
    q.id = `${deck.id}-${i}`;
    if (deck.passage) q.passage = deck.passage;
  });
});

const ALL_QUESTIONS = {};
ALL_DECKS.forEach((d) => d.questions.forEach((q) => { ALL_QUESTIONS[q.id] = q; }));

const DIFFICULTIES = ["easy", "medium", "hard"];
function difficultyOf(q) {
  return DIFFICULTIES.includes(q.difficulty) ? q.difficulty : "medium";
}

function appendFigure(container, q) {
  if (!q.figure) return;
  const fig = document.createElement("div");
  fig.className = "figure";
  fig.innerHTML = q.figure; // trusted SVG/HTML produced by our own renderer
  container.appendChild(fig);
  if (q.figure_caption) {
    const cap = document.createElement("div");
    cap.className = "figure-caption";
    cap.textContent = q.figure_caption;
    container.appendChild(cap);
  }
}

// ---------- persistent state (localStorage) ----------
function loadState() {
  try {
    return JSON.parse(localStorage.getItem(STORE_KEY)) || { cards: {}, saved: [] };
  } catch {
    return { cards: {}, saved: [] };
  }
}

function saveState(state) {
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify(state));
  } catch {
    // ignore storage failures (private browsing, quota, etc.)
  }
}

function getCard(qid) {
  const s = loadState();
  return s.cards[qid] || {
    interval: 0, ease: 2.5, reps: 0, lapses: 0, due: 0,
    lastGrade: null, lastCorrect: null, seen: 0, missed: 0,
  };
}

function setCard(qid, card) {
  const s = loadState();
  s.cards[qid] = card;
  saveState(s);
}

function isSaved(qid) {
  return loadState().saved.includes(qid);
}

function toggleSaved(qid) {
  const s = loadState();
  const i = s.saved.indexOf(qid);
  if (i >= 0) s.saved.splice(i, 1);
  else s.saved.push(qid);
  saveState(s);
}

// ---------- Anki-style SM-2 scheduler ----------
function applyGrade(qid, grade) {
  const card = getCard(qid);
  card.seen += 1;
  card.lastGrade = grade;

  if (grade === "again") {
    card.lastCorrect = false;
    card.missed += 1;
    card.reps = 0;
    card.lapses += 1;
    card.ease = Math.max(MIN_EASE, card.ease - 0.2);
    card.interval = 10 / (60 * 24); // 10 minutes (relearn)
    card.due = Date.now() + 10 * 60 * 1000;
  } else {
    card.lastCorrect = true;
    if (grade === "hard") {
      card.ease = Math.max(MIN_EASE, card.ease - 0.15);
      card.interval = card.reps === 0 ? 1 : Math.max(card.interval, 0.5) * 1.2;
      card.reps += 1;
    } else if (grade === "good") {
      if (card.reps === 0) card.interval = 1;
      else if (card.reps === 1) card.interval = 6;
      else card.interval = card.interval * card.ease;
      card.reps += 1;
    } else { // easy
      card.ease = Math.min(3.0, card.ease + 0.15);
      card.interval = card.reps === 0 ? 4 : card.interval * card.ease * 1.3;
      card.reps += 1;
    }
    card.due = Date.now() + Math.round(card.interval * DAY_MS);
  }

  setCard(qid, card);
}

// ---------- derived decks ----------
function getDueQuestions() {
  const s = loadState();
  const now = Date.now();
  const out = [];
  ALL_DECKS.forEach((d) => d.questions.forEach((q) => {
    const c = s.cards[q.id];
    if (c && c.due && c.due <= now) out.push(q);
  }));
  return out;
}

function getMissedQuestions() {
  const s = loadState();
  const out = [];
  ALL_DECKS.forEach((d) => d.questions.forEach((q) => {
    const c = s.cards[q.id];
    if (c && c.lastCorrect === false) out.push(q);
  }));
  return out;
}

function getSavedQuestions() {
  const s = loadState();
  return s.saved.map((id) => ALL_QUESTIONS[id]).filter(Boolean);
}

function getByDifficulty(diff) {
  const out = [];
  ALL_DECKS.forEach((d) => d.questions.forEach((q) => {
    if (difficultyOf(q) === diff) out.push(q);
  }));
  return out;
}

function getFullLengthDecks() {
  return typeof FULL_DECKS !== "undefined" ? FULL_DECKS : [];
}

function sectionSeconds(section) {
  if (/CARS|Critical Analysis/i.test(section)) return 90 * 60;
  return 95 * 60;
}

function formatTime(sec) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function countDue(deck) {
  const s = loadState();
  const now = Date.now();
  return deck.questions.filter((q) => {
    const c = s.cards[q.id];
    return c && c.due && c.due <= now;
  }).length;
}

function countNew(deck) {
  const s = loadState();
  return deck.questions.filter((q) => {
    const c = s.cards[q.id];
    return !c || c.due === 0;
  }).length;
}

function renderHome() {
  activeDeck = null;
  progressLabel.textContent = "";
  root.innerHTML = "";
  root.classList.add("home");

  const heading = document.createElement("p");
  heading.className = "home-heading";
  heading.textContent = "Choose a deck";
  root.appendChild(heading);

  const due = getDueQuestions();
  const missed = getMissedQuestions();
  const saved = getSavedQuestions();

  const specials = [];
  if (due.length) {
    specials.push({
      title: "Review (Anki)",
      section: `${due.length} due card${due.length === 1 ? "" : "s"}`,
      deck: { id: "due", title: "Review (Anki)", section: "Due for review", questions: due },
    });
  }
  if (missed.length) {
    specials.push({
      title: "Review Missed",
      section: `${missed.length} card${missed.length === 1 ? "" : "s"} you got wrong`,
      deck: { id: "missed", title: "Review Missed", section: "Cards you got wrong", questions: missed },
    });
  }
  if (saved.length) {
    specials.push({
      title: "Saved",
      section: `${saved.length} bookmarked card${saved.length === 1 ? "" : "s"}`,
      deck: { id: "saved", title: "Saved", section: "Bookmarked questions", questions: saved },
    });
  }

  specials.forEach((sp) => {
    const b = document.createElement("button");
    b.className = "set-card special-card";
    b.innerHTML = `<span class="set-title">${sp.title}</span><span class="set-section">${sp.section}</span>`;
    b.addEventListener("click", () => startDeck(sp.deck));
    root.appendChild(b);
  });

  // --- Practice by difficulty ---
  const diffHeading = document.createElement("p");
  diffHeading.className = "home-heading";
  diffHeading.textContent = "Practice by difficulty";
  root.appendChild(diffHeading);

  const diffGrid = document.createElement("div");
  diffGrid.className = "set-grid";
  DIFFICULTIES.forEach((diff) => {
    const qs = getByDifficulty(diff);
    if (!qs.length) return;
    const label = diff.charAt(0).toUpperCase() + diff.slice(1);
    const card = document.createElement("button");
    card.className = "set-card";
    card.innerHTML = `
      <span class="set-title">${label}</span>
      <span class="set-section">${qs.length} questions</span>
      <span class="diff-tag diff-${diff}">${diff}</span>
    `;
    card.addEventListener("click", () => startDeck({ id: `diff-${diff}`, title: label, section: "Practice by difficulty", questions: qs }));
    diffGrid.appendChild(card);
  });
  root.appendChild(diffGrid);

  // --- Practice Tests (full-length, timed) ---
  const testHeading = document.createElement("p");
  testHeading.className = "home-heading";
  testHeading.textContent = "Practice Tests (timed)";
  root.appendChild(testHeading);

  const testGrid = document.createElement("div");
  testGrid.className = "set-grid";
  getFullLengthDecks().forEach((deck) => {
    const card = document.createElement("button");
    card.className = "set-card";
    card.innerHTML = `
      <span class="set-title">${deck.title}</span>
      <span class="set-section">${deck.section}</span>
      <span class="set-count">${deck.questions.length} questions · timed</span>
    `;
    card.addEventListener("click", () => startTest(deck));
    testGrid.appendChild(card);
  });
  root.appendChild(testGrid);

  // --- Hard / complex scenarios ---
  const hardDecks = (typeof HARD_DECKS !== "undefined" ? HARD_DECKS : []);
  if (hardDecks.length) {
    const hardHeading = document.createElement("p");
    hardHeading.className = "home-heading";
    hardHeading.textContent = "Hard scenarios";
    root.appendChild(hardHeading);

    const hardGrid = document.createElement("div");
    hardGrid.className = "set-grid";
    hardDecks.forEach((deck) => {
      const card = document.createElement("button");
      card.className = "set-card";
      card.innerHTML = `
        <span class="set-title">${deck.title}</span>
        <span class="set-section">${deck.section}</span>
        <span class="set-count">${deck.questions.length} questions · untimed</span>
      `;
      card.addEventListener("click", () => startDeck(deck));
      hardGrid.appendChild(card);
    });
    root.appendChild(hardGrid);
  }

  // --- Topic decks ---
  const topicHeading = document.createElement("p");
  topicHeading.className = "home-heading";
  topicHeading.textContent = "Topic decks";
  root.appendChild(topicHeading);

  const grid = document.createElement("div");
  grid.className = "set-grid";

  (typeof DECKS !== "undefined" ? DECKS : []).forEach((deck) => {
    const dueCount = countDue(deck);
    const newCount = countNew(deck);
    const card = document.createElement("button");
    card.className = "set-card";
    card.innerHTML = `
      <span class="set-title">${deck.title}</span>
      <span class="set-section">${deck.section}</span>
      <span class="set-count">${deck.questions.length} cards</span>
      <span class="badges">
        ${dueCount ? `<span class="set-due">${dueCount} due</span>` : ""}
        ${newCount ? `<span class="set-new">${newCount} new</span>` : ""}
      </span>
    `;
    card.addEventListener("click", () => startDeck(deck));
    grid.appendChild(card);
  });

  root.appendChild(grid);
}

function startDeck(deck) {
  root.classList.remove("home");
  stopTimer();
  testMode = false;
  activeDeck = deck;
  current = 0;
  sessionCorrect = 0;
  render();
}

function render() {
  if (!activeDeck || activeDeck.questions.length === 0) {
    renderEmpty();
    return;
  }
  if (current >= activeDeck.questions.length) {
    renderSummary();
    return;
  }

  const q = activeDeck.questions[current];
  progressLabel.textContent = `${activeDeck.title} · Card ${current + 1} of ${activeDeck.questions.length} · Correct: ${sessionCorrect}`;

  root.innerHTML = "";
  answered = false;

  const header = document.createElement("div");
  header.className = "card-header";

  const indexEl = document.createElement("div");
  indexEl.className = "q-index";
  indexEl.innerHTML = `${activeDeck.section} · Card ${current + 1} <span class="q-type-tag">${q.passage ? "Passage-based" : "Discrete"}</span> <span class="diff-tag diff-${difficultyOf(q)}">${difficultyOf(q)}</span>`;
  header.appendChild(indexEl);

  const saveBtn = document.createElement("button");
  const savedNow = isSaved(q.id);
  saveBtn.className = "save-btn" + (savedNow ? " saved" : "");
  saveBtn.textContent = savedNow ? "★ Saved" : "☆ Save";
  saveBtn.addEventListener("click", () => {
    toggleSaved(q.id);
    const nowSaved = isSaved(q.id);
    saveBtn.classList.toggle("saved", nowSaved);
    saveBtn.textContent = nowSaved ? "★ Saved" : "☆ Save";
  });
  header.appendChild(saveBtn);
  root.appendChild(header);

  if (q.passage) {
    const p = document.createElement("div");
    p.className = "passage";
    p.textContent = q.passage;
    root.appendChild(p);
  }

  appendFigure(root, q);

  const qText = document.createElement("p");
  qText.className = "q-text";
  qText.textContent = q.question;
  root.appendChild(qText);

  const optionsEl = document.createElement("div");
  optionsEl.className = "options";
  const letters = ["A", "B", "C", "D"];
  q.options.forEach((optionText, i) => {
    const b = document.createElement("button");
    b.className = "option";
    b.innerHTML = `<span class="option-letter">${letters[i]}</span><span class="option-text">${optionText}</span>`;
    b.addEventListener("click", () => selectOption(i, b, optionsEl));
    optionsEl.appendChild(b);
  });
  root.appendChild(optionsEl);
}

function selectOption(i, btn, optionsEl) {
  if (answered) return;
  answered = true;

  const q = activeDeck.questions[current];
  const wasCorrect = i === q.correct;
  if (wasCorrect) sessionCorrect++;

  const allButtons = optionsEl.querySelectorAll(".option");
  allButtons.forEach((b, idx) => {
    b.disabled = true;
    if (idx === q.correct) b.classList.add("correct");
    else if (idx === i) b.classList.add("wrong");
  });

  progressLabel.textContent = `${activeDeck.title} · Card ${current + 1} of ${activeDeck.questions.length} · Correct: ${sessionCorrect}`;

  const letters = ["A", "B", "C", "D"];
  const explanation = document.createElement("div");
  explanation.className = "explanation";
  explanation.innerHTML = `<strong>${wasCorrect ? "Correct" : "Not quite"} — answer: ${letters[q.correct]}.</strong> ${q.explanation}`;
  root.appendChild(explanation);

  showGradeButtons(wasCorrect);
}

function showGradeButtons(wasCorrect) {
  const row = document.createElement("div");
  row.className = "grade-row";
  const grades = [
    { key: "again", label: "Again" },
    { key: "hard", label: "Hard" },
    { key: "good", label: "Good" },
    { key: "easy", label: "Easy" },
  ];
  grades.forEach((g) => {
    const b = document.createElement("button");
    b.className = "grade-btn grade-" + g.key;
    b.textContent = g.label;
    if ((g.key === "again" && !wasCorrect) || (g.key === "good" && wasCorrect)) {
      b.classList.add("suggested");
    }
    b.addEventListener("click", () => gradeAndNext(g.key));
    row.appendChild(b);
  });
  root.appendChild(row);
}

function gradeAndNext(grade) {
  applyGrade(activeDeck.questions[current].id, grade);
  current++;
  render();
}

function startTest(deck) {
  root.classList.remove("home");
  stopTimer();
  activeDeck = deck;
  current = 0;
  testMode = true;
  testAnswers = [];
  testSecondsLeft = sectionSeconds(deck.section);
  renderTest();
  startTimer();
}

function startTimer() {
  stopTimer();
  testTimer = setInterval(() => {
    testSecondsLeft--;
    const el = document.getElementById("test-timer");
    if (el) el.textContent = formatTime(testSecondsLeft);
    if (testSecondsLeft <= 0) {
      stopTimer();
      finishTest();
    }
  }, 1000);
}

function stopTimer() {
  if (testTimer) {
    clearInterval(testTimer);
    testTimer = null;
  }
}

function renderTest() {
  if (current >= activeDeck.questions.length) {
    finishTest();
    return;
  }

  const q = activeDeck.questions[current];
  progressLabel.textContent = `${activeDeck.title} · Question ${current + 1} of ${activeDeck.questions.length}`;

  root.innerHTML = "";
  answered = false;

  const header = document.createElement("div");
  header.className = "card-header";

  const indexEl = document.createElement("div");
  indexEl.className = "q-index";
  indexEl.textContent = `${activeDeck.section} · Question ${current + 1}`;
  header.appendChild(indexEl);

  const timerEl = document.createElement("span");
  timerEl.className = "test-timer";
  timerEl.id = "test-timer";
  timerEl.textContent = formatTime(testSecondsLeft);
  header.appendChild(timerEl);
  root.appendChild(header);

  if (q.passage) {
    const p = document.createElement("div");
    p.className = "passage";
    p.textContent = q.passage;
    root.appendChild(p);
  }

  appendFigure(root, q);

  const qText = document.createElement("p");
  qText.className = "q-text";
  qText.textContent = q.question;
  root.appendChild(qText);

  const optionsEl = document.createElement("div");
  optionsEl.className = "options";
  const letters = ["A", "B", "C", "D"];
  q.options.forEach((optionText, i) => {
    const b = document.createElement("button");
    b.className = "option";
    b.innerHTML = `<span class="option-letter">${letters[i]}</span><span class="option-text">${optionText}</span>`;
    b.addEventListener("click", () => selectTestOption(i, b, optionsEl));
    optionsEl.appendChild(b);
  });
  root.appendChild(optionsEl);
}

function selectTestOption(i, btn, optionsEl) {
  if (answered) return;
  answered = true;

  const q = activeDeck.questions[current];
  const wasCorrect = i === q.correct;
  testAnswers.push({ id: q.id, wasCorrect });

  const allButtons = optionsEl.querySelectorAll(".option");
  allButtons.forEach((b, idx) => {
    b.disabled = true;
    if (idx === q.correct) b.classList.add("correct");
    else if (idx === i) b.classList.add("wrong");
  });

  current++;
  setTimeout(() => renderTest(), 350);
}

function finishTest() {
  stopTimer();
  testMode = false;

  const results = testAnswers;
  const correctCount = results.filter((a) => a.wasCorrect).length;
  const total = results.length;
  const missedIds = results.filter((a) => !a.wasCorrect).map((a) => a.id);

  // Feed the SRS: correct -> "good", wrong -> "again".
  results.forEach((a) => applyGrade(a.id, a.wasCorrect ? "good" : "again"));

  progressLabel.textContent = "";
  root.innerHTML = "";

  const wrap = document.createElement("div");
  wrap.className = "summary";

  const setLabel = document.createElement("div");
  setLabel.className = "q-index";
  setLabel.textContent = activeDeck.title;
  wrap.appendChild(setLabel);

  const scoreEl = document.createElement("div");
  scoreEl.className = "score";
  scoreEl.innerHTML = `<span>${correctCount}</span> / ${total}`;
  wrap.appendChild(scoreEl);

  const msg = document.createElement("p");
  msg.textContent = pickMessage(correctCount, total);
  wrap.appendChild(msg);

  const note = document.createElement("p");
  note.className = "srs-note";
  note.textContent = "Missed questions were saved to Review Missed for later practice.";
  wrap.appendChild(note);

  const btnRow = document.createElement("div");
  btnRow.className = "summary-actions";

  if (missedIds.length) {
    const reviewBtn = document.createElement("button");
    reviewBtn.className = "next-btn";
    reviewBtn.textContent = `Review ${missedIds.length} missed`;
    reviewBtn.addEventListener("click", () => {
      const missedQs = missedIds.map((id) => ALL_QUESTIONS[id]).filter(Boolean);
      startDeck({ id: "test-missed", title: "Test Missed", section: "Missed from test", questions: missedQs });
    });
    btnRow.appendChild(reviewBtn);
  }

  const homeBtn = document.createElement("button");
  homeBtn.className = "restart-btn";
  homeBtn.textContent = "All decks";
  homeBtn.addEventListener("click", renderHome);
  btnRow.appendChild(homeBtn);

  wrap.appendChild(btnRow);
  root.appendChild(wrap);
}

function renderSummary() {
  progressLabel.textContent = "";
  root.innerHTML = "";

  const wrap = document.createElement("div");
  wrap.className = "summary";

  const setLabel = document.createElement("div");
  setLabel.className = "q-index";
  setLabel.textContent = activeDeck.title;
  wrap.appendChild(setLabel);

  const scoreEl = document.createElement("div");
  scoreEl.className = "score";
  scoreEl.innerHTML = `<span>${sessionCorrect}</span> / ${activeDeck.questions.length}`;
  wrap.appendChild(scoreEl);

  const msg = document.createElement("p");
  msg.textContent = pickMessage(sessionCorrect, activeDeck.questions.length);
  wrap.appendChild(msg);

  const note = document.createElement("p");
  note.className = "srs-note";
  note.textContent = "Cards were rescheduled with spaced repetition — revisit the due cards later to lock them into memory.";
  wrap.appendChild(note);

  const btnRow = document.createElement("div");
  btnRow.className = "summary-actions";

  const retryBtn = document.createElement("button");
  retryBtn.className = "restart-btn";
  retryBtn.textContent = "Retry this deck";
  retryBtn.addEventListener("click", () => startDeck(activeDeck));
  btnRow.appendChild(retryBtn);

  const homeBtn = document.createElement("button");
  homeBtn.className = "next-btn";
  homeBtn.textContent = "All decks";
  homeBtn.addEventListener("click", renderHome);
  btnRow.appendChild(homeBtn);

  wrap.appendChild(btnRow);
  root.appendChild(wrap);
}

function renderEmpty() {
  progressLabel.textContent = "";
  root.innerHTML = "";

  const wrap = document.createElement("div");
  wrap.className = "summary";

  const msg = document.createElement("p");
  msg.textContent = "Nothing to review right now. Study a deck, and cards you need to review will appear here.";
  wrap.appendChild(msg);

  const homeBtn = document.createElement("button");
  homeBtn.className = "next-btn";
  homeBtn.textContent = "All decks";
  homeBtn.addEventListener("click", renderHome);
  wrap.appendChild(homeBtn);

  root.appendChild(wrap);
}

function pickMessage(s, total) {
  const ratio = s / total;
  if (ratio === 1) return "Perfect score on this deck.";
  if (ratio >= 0.7) return "Strong performance — just a few concepts to review.";
  if (ratio >= 0.4) return "A mixed result — worth revisiting this section's core concepts.";
  return "This section needs more review before test day.";
}

const resetLink = document.getElementById("reset-progress");
if (resetLink) {
  resetLink.addEventListener("click", (e) => {
    e.preventDefault();
    if (confirm("Clear all progress, saved cards, and the review schedule?")) {
      localStorage.removeItem(STORE_KEY);
      renderHome();
    }
  });
}

renderHome();



