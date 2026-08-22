const root = document.getElementById("quiz-root");
const progressLabel = document.getElementById("progress-label");

let activeSet = null;
let current = 0;
let score = 0;
let answered = false;

function renderHome() {
  activeSet = null;
  progressLabel.textContent = "";
  root.innerHTML = "";
  root.classList.add("home");

  const heading = document.createElement("p");
  heading.className = "home-heading";
  heading.textContent = "Choose a practice set";
  root.appendChild(heading);

  const grid = document.createElement("div");
  grid.className = "set-grid";

  PRACTICE_SETS.forEach((set) => {
    const card = document.createElement("button");
    card.className = "set-card";
    card.innerHTML = `
      <span class="set-title">${set.title}</span>
      <span class="set-section">${set.section}</span>
      <span class="set-count">${set.questions.length} questions</span>
    `;
    card.addEventListener("click", () => startSet(set));
    grid.appendChild(card);
  });

  root.appendChild(grid);
}

function startSet(set) {
  root.classList.remove("home");
  activeSet = set;
  current = 0;
  score = 0;
  render();
}

function render() {
  if (current >= activeSet.questions.length) {
    renderSummary();
    return;
  }

  const q = activeSet.questions[current];
  progressLabel.textContent = `${activeSet.title} · Question ${current + 1} of ${activeSet.questions.length} · Score: ${score}`;

  root.innerHTML = "";
  answered = false;

  const indexEl = document.createElement("div");
  indexEl.className = "q-index";
  indexEl.textContent = `${activeSet.section} · Question ${current + 1}`;
  root.appendChild(indexEl);

  if (activeSet.passage && current === 0) {
    const passageEl = document.createElement("div");
    passageEl.className = "passage";
    passageEl.textContent = activeSet.passage;
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

  const q = activeSet.questions[current];
  const allButtons = optionsEl.querySelectorAll(".option");
  allButtons.forEach((b, idx) => {
    b.disabled = true;
    if (idx === q.correct) b.classList.add("correct");
    else if (idx === i) b.classList.add("wrong");
  });

  if (i === q.correct) score++;
  progressLabel.textContent = `${activeSet.title} · Question ${current + 1} of ${activeSet.questions.length} · Score: ${score}`;

  const explanation = document.createElement("div");
  explanation.className = "explanation";
  explanation.innerHTML = `<strong>${i === q.correct ? "Correct." : "Not quite."}</strong> ${q.explanation}`;
  root.appendChild(explanation);

  const actions = document.createElement("div");
  actions.className = "actions";
  const nextBtn = document.createElement("button");
  nextBtn.className = "next-btn";
  nextBtn.textContent = current === activeSet.questions.length - 1 ? "See results" : "Next question";
  nextBtn.addEventListener("click", () => {
    current++;
    render();
  });
  actions.appendChild(nextBtn);
  root.appendChild(actions);
}

function renderSummary() {
  progressLabel.textContent = "";
  root.innerHTML = "";

  const wrap = document.createElement("div");
  wrap.className = "summary";

  const setLabel = document.createElement("div");
  setLabel.className = "q-index";
  setLabel.textContent = activeSet.title;
  wrap.appendChild(setLabel);

  const scoreEl = document.createElement("div");
  scoreEl.className = "score";
  scoreEl.innerHTML = `<span>${score}</span> / ${activeSet.questions.length}`;
  wrap.appendChild(scoreEl);

  const msg = document.createElement("p");
  msg.textContent = pickMessage(score, activeSet.questions.length);
  wrap.appendChild(msg);

  const btnRow = document.createElement("div");
  btnRow.className = "summary-actions";

  const retryBtn = document.createElement("button");
  retryBtn.className = "restart-btn";
  retryBtn.textContent = "Retry this set";
  retryBtn.addEventListener("click", () => startSet(activeSet));
  btnRow.appendChild(retryBtn);

  const homeBtn = document.createElement("button");
  homeBtn.className = "next-btn";
  homeBtn.textContent = "All practice sets";
  homeBtn.addEventListener("click", renderHome);
  btnRow.appendChild(homeBtn);

  wrap.appendChild(btnRow);
  root.appendChild(wrap);
}

function pickMessage(s, total) {
  const ratio = s / total;
  if (ratio === 1) return "Perfect score on this set.";
  if (ratio >= 0.7) return "Strong performance — just a few concepts to review.";
  if (ratio >= 0.4) return "A mixed result — worth revisiting this section's core concepts.";
  return "This section needs more review before test day.";
}

renderHome();
