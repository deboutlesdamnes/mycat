const root = document.getElementById("quiz-root");
const progressLabel = document.getElementById("progress-label");
const STORAGE_KEY = "mycat_progress_v1";

let activeDeck = null;
let current = 0;
let score = 0;
let answered = false;

// Give every question a stable id and carry its deck's passage (if any)
// onto each question so context still shows up when reviewed out of order.
DECKS.forEach((deck) => {
  deck.questions.forEach((q, i) => {
    q.id = `${deck.id}-${i}`;
    if (deck.passage) q.passage = deck.passage;
  });
});

function loadProgress() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

function saveProgress(progress) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  } catch {
    // ignore storage failures (private browsing, quota, etc.)
  }
}

function recordAnswer(questionId, wasCorrect) {
  const progress = loadProgress();
  const entry = progress[questionId] || { timesSeen: 0, timesMissed: 0, missed: false };
  entry.timesSeen += 1;
  entry.missed = !wasCorrect;
  if (!wasCorrect) entry.timesMissed += 1;
  progress[questionId] = entry;
  saveProgress(progress);
}

function getMissedCount(deck) {
  const progress = loadProgress();
  return deck.questions.filter((q) => progress[q.id] && progress[q.id].missed).length;
}

function buildMissedDeck() {
  const progress = loadProgress();
  const missedQuestions = [];
  DECKS.forEach((deck) => {
    deck.questions.forEach((q) => {
      if (progress[q.id] && progress[q.id].missed) missedQuestions.push(q);
    });
  });
  return {
    id: "missed-review",
    title: "Review Missed",
    section: "Cards you got wrong last time",
    questions: missedQuestions
  };
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

  const totalMissed = DECKS.reduce((sum, deck) => sum + getMissedCount(deck), 0);
  if (totalMissed > 0) {
    const missedCard = document.createElement("button");
    missedCard.className = "set-card missed-card";
    missedCard.innerHTML = `
      <span class="set-title">Review Missed</span>
      <span class="set-section">Cards you got wrong last time</span>
      <span class="set-count">${totalMissed} card${totalMissed === 1 ? "" : "s"}</span>
    `;
    missedCard.addEventListener("click", () => startDeck(buildMissedDeck()));
    root.appendChild(missedCard);
  }

  const grid = document.createElement("div");
  grid.className = "set-grid";

  DECKS.forEach((deck) => {
    const missedCount = getMissedCount(deck);
    const card = document.createElement("button");
    card.className = "set-card";
    card.innerHTML = `
      <span class="set-title">${deck.title}</span>
      <span class="set-section">${deck.section}</span>
      <span class="set-count">${deck.questions.length} cards</span>
      ${missedCount > 0 ? `<span class="set-missed">${missedCount} missed last time</span>` : ""}
    `;
    card.addEventListener("click", () => startDeck(deck));
    grid.appendChild(card);
  });

  root.appendChild(grid);
}

function startDeck(deck) {
  root.classList.remove("home");
  activeDeck = deck;
  current = 0;
  score = 0;
  render();
}

function render() {
  if (activeDeck.questions.length === 0) {
    renderEmpty();
    return;
  }
  if (current >= activeDeck.questions.length) {
    renderSummary();
    return;
  }

  const q = activeDeck.questions[current];
  progressLabel.textContent = `${activeDeck.title} · Card ${current + 1} of ${activeDeck.questions.length} · Score: ${score}`;

  root.innerHTML = "";
  answered = false;

  const indexEl = document.createElement("div");
  indexEl.className = "q-index";
  indexEl.textContent = `${activeDeck.section} · Card ${current + 1}`;
  root.appendChild(indexEl);

  if (q.passage) {
    const passageEl = document.createElement("div");
    passageEl.className = "passage";
    passageEl.textContent = q.passage;
    root.appendChild(passageEl);
  }

  const qText = document.createElement("p");
  qText.className = "q-text";
  qText.textContent = q.question;
  root.appendChild(qText);

  const optionsEl = document.createElement("div");
  optionsEl.className = "options";
  q.options.forEach((optionText, i) => {
    const btn = document.createElement("button");
    btn.className = "option";
    btn.textContent = optionText;
    btn.addEventListener("click", () => selectOption(i, btn, optionsEl));
    optionsEl.appendChild(btn);
  });
  root.appendChild(optionsEl);
}

function selectOption(i, btn, optionsEl) {
  if (answered) return;
  answered = true;

  const q = activeDeck.questions[current];
  const wasCorrect = i === q.correct;
  recordAnswer(q.id, wasCorrect);

  const allButtons = optionsEl.querySelectorAll(".option");
  allButtons.forEach((b, idx) => {
    b.disabled = true;
    if (idx === q.correct) b.classList.add("correct");
    else if (idx === i) b.classList.add("wrong");
  });

  if (wasCorrect) score++;
  progressLabel.textContent = `${activeDeck.title} · Card ${current + 1} of ${activeDeck.questions.length} · Score: ${score}`;

  const explanation = document.createElement("div");
  explanation.className = "explanation";
  explanation.innerHTML = `<strong>${wasCorrect ? "Correct." : "Not quite."}</strong> ${q.explanation}`;
  root.appendChild(explanation);

  const actions = document.createElement("div");
  actions.className = "actions";
  const nextBtn = document.createElement("button");
  nextBtn.className = "next-btn";
  nextBtn.textContent = current === activeDeck.questions.length - 1 ? "See results" : "Next card";
  nextBtn.addEventListener("click", () => {
    current++;
    render();
  });
  actions.appendChild(nextBtn);
  root.appendChild(actions);
}

function renderEmpty() {
  progressLabel.textContent = "";
  root.innerHTML = "";
  const wrap = document.createElement("div");
  wrap.className = "summary";
  const msg = document.createElement("p");
  msg.textContent = "No missed cards right now — clear a few decks first, and anything you get wrong will show up here.";
  wrap.appendChild(msg);
  const homeBtn = document.createElement("button");
  homeBtn.className = "next-btn";
  homeBtn.textContent = "All decks";
  homeBtn.addEventListener("click", renderHome);
  wrap.appendChild(homeBtn);
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
  scoreEl.innerHTML = `<span>${score}</span> / ${activeDeck.questions.length}`;
  wrap.appendChild(scoreEl);

  const msg = document.createElement("p");
  msg.textContent = pickMessage(score, activeDeck.questions.length);
  wrap.appendChild(msg);

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
    if (confirm("Clear all tracked progress and missed cards?")) {
      localStorage.removeItem(STORAGE_KEY);
      renderHome();
    }
  });
}

renderHome();
