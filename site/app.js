const root = document.getElementById("quiz-root");
const progressLabel = document.getElementById("progress-label");

let current = 0;
let score = 0;
let answered = false;

function render() {
  if (current >= QUESTIONS.length) {
    renderSummary();
    return;
  }

  const q = QUESTIONS[current];
  progressLabel.textContent = `Question ${current + 1} of ${QUESTIONS.length} · Score: ${score}`;

  root.innerHTML = "";
  answered = false;

  const indexEl = document.createElement("div");
  indexEl.className = "q-index";
  indexEl.textContent = `Question ${current + 1}`;
  root.appendChild(indexEl);

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

  const q = QUESTIONS[current];
  const allButtons = optionsEl.querySelectorAll(".option");
  allButtons.forEach((b, idx) => {
    b.disabled = true;
    if (idx === q.correct) b.classList.add("correct");
    else if (idx === i) b.classList.add("wrong");
  });

  if (i === q.correct) score++;
  progressLabel.textContent = `Question ${current + 1} of ${QUESTIONS.length} · Score: ${score}`;

  const explanation = document.createElement("div");
  explanation.className = "explanation";
  explanation.innerHTML = `<strong>${i === q.correct ? "Correct." : "Not quite."}</strong> ${q.explanation}`;
  root.appendChild(explanation);

  const actions = document.createElement("div");
  actions.className = "actions";
  const nextBtn = document.createElement("button");
  nextBtn.className = "next-btn";
  nextBtn.textContent = current === QUESTIONS.length - 1 ? "See results" : "Next question";
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

  const scoreEl = document.createElement("div");
  scoreEl.className = "score";
  scoreEl.innerHTML = `<span>${score}</span> / ${QUESTIONS.length}`;
  wrap.appendChild(scoreEl);

  const msg = document.createElement("p");
  msg.textContent = pickMessage(score, QUESTIONS.length);
  wrap.appendChild(msg);

  const restartBtn = document.createElement("button");
  restartBtn.className = "restart-btn";
  restartBtn.textContent = "Try again";
  restartBtn.addEventListener("click", () => {
    current = 0;
    score = 0;
    render();
  });
  wrap.appendChild(restartBtn);

  root.appendChild(wrap);
}

function pickMessage(s, total) {
  const ratio = s / total;
  if (ratio === 1) return "Perfect score — no myth got past you.";
  if (ratio >= 0.7) return "Solid instincts for spotting a misconception.";
  if (ratio >= 0.4) return "A mixed bag — plenty of common myths are stickier than they look.";
  return "These myths are more convincing than they should be — even smart people fall for them.";
}

render();
