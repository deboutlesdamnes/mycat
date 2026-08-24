(function () {
  renderNav("practice");
  const root = document.getElementById("page-root");
  const params = new URLSearchParams(location.search);
  const mode = params.get("mode");

  let queue = [];
  let idx = 0;
  let answered = false;
  let startedAt = 0;
  let setLabel = "Practice";
  let setPassage = null;
  let sessionCorrect = 0;
  let timerHandle = null;
  let elapsedSec = 0;

  function buildQueue() {
    const store = Store.load();
    if (mode === "due") {
      setLabel = "Review due cards";
      return Stats.dueCards(store).map((d) => Data.allQuestions[d.qid]).filter(Boolean);
    }
    if (mode === "missed") {
      setLabel = "Review missed";
      return Object.entries(store.cards).filter(([, c]) => c.lastCorrect === false)
        .map(([id]) => Data.allQuestions[id]).filter(Boolean);
    }
    if (mode === "flagged") {
      setLabel = "Flagged questions";
      return store.flagged.map((id) => Data.allQuestions[id]).filter(Boolean);
    }
    if (mode === "saved") {
      setLabel = "Saved";
      return store.saved.map((id) => Data.allQuestions[id]).filter(Boolean);
    }
    if (mode === "topic") {
      const topic = params.get("topic") || "";
      setLabel = `Weak-area drill · ${topic}`;
      const qs = Object.values(Data.allQuestions).filter((q) => q.topic === topic);
      qs.sort((a, b) => {
        const rank = (q) => { const c = store.cards[q.id]; if (!c) return 0; return c.lastCorrect === false ? 1 : 2; };
        return rank(a) - rank(b);
      });
      return qs;
    }
    if (mode === "section") {
      const section = params.get("section") || "";
      setLabel = section;
      const deckWithPassage = Data.allDecks.find((d) => d.section === section && d.passage);
      if (deckWithPassage) { setPassage = deckWithPassage.passage; return deckWithPassage.questions; }
      return Object.values(Data.allQuestions).filter((q) => q.section === section);
    }
    if (mode === "deck") {
      const id = params.get("id") || "";
      const deck = Data.allDecks.find((d) => d.id === id);
      if (deck) { setLabel = deck.title; setPassage = deck.passage || null; return deck.questions; }
      return [];
    }
    if (mode === "diff") {
      const value = params.get("value") || "";
      setLabel = value.charAt(0).toUpperCase() + value.slice(1) + " questions";
      return Object.values(Data.allQuestions).filter((q) => Data.difficultyOf(q) === value);
    }
    return null;
  }

  function renderPicker() {
    const store = Store.load();
    const due = Stats.dueCards(store);
    const missedCount = Object.values(store.cards).filter((c) => c.lastCorrect === false).length;

    const specials = [];
    if (due.length) specials.push({ title: "Review (due)", sub: `${due.length} card${due.length === 1 ? "" : "s"} due`, href: "practice.html?mode=due" });
    if (missedCount) specials.push({ title: "Review missed", sub: `${missedCount} card${missedCount === 1 ? "" : "s"} you got wrong`, href: "practice.html?mode=missed" });
    if (store.flagged.length) specials.push({ title: "Flagged", sub: `${store.flagged.length} flagged`, href: "practice.html?mode=flagged" });
    if (store.saved.length) specials.push({ title: "Saved", sub: `${store.saved.length} bookmarked`, href: "practice.html?mode=saved" });

    const byDiff = Data.DIFFICULTIES.map((d) => ({
      d, n: Object.values(Data.allQuestions).filter((q) => Data.difficultyOf(q) === d).length,
    })).filter((x) => x.n);

    const bySection = Data.SECTIONS.map((s) => ({
      s, n: Object.values(Data.allQuestions).filter((q) => q.section === s).length,
    })).filter((x) => x.n);

    root.innerHTML = `
      <div class="page-head"><h2 style="margin:0">Practice</h2></div>
      ${specials.length ? `
        <div>
          <div class="k" style="margin-bottom:10px">Continue where you left off</div>
          <div class="deck-grid">
            ${specials.map((s) => `<a class="deck-tile" href="${s.href}"><span class="deck-tile-title">${s.title}</span><span class="deck-tile-sub">${s.sub}</span></a>`).join("")}
          </div>
        </div>` : ""}
      <div>
        <div class="k" style="margin-bottom:10px">By section</div>
        <div class="deck-grid">
          ${bySection.map((x) => `<a class="deck-tile" href="practice.html?mode=section&section=${encodeURIComponent(x.s)}"><span class="deck-tile-title">${x.s.replace(" Foundations", "")}</span><span class="deck-tile-count">${x.n} questions</span></a>`).join("")}
        </div>
      </div>
      <div>
        <div class="k" style="margin-bottom:10px">By difficulty</div>
        <div class="deck-grid">
          ${byDiff.map((x) => `<a class="deck-tile" href="practice.html?mode=diff&value=${x.d}"><span class="deck-tile-title">${x.d[0].toUpperCase() + x.d.slice(1)}</span><span class="deck-tile-count">${x.n} questions</span></a>`).join("")}
        </div>
      </div>
      <div>
        <div class="k" style="margin-bottom:10px">Topic decks</div>
        <div class="deck-grid">
          ${Data.decks.map((deck) => `<a class="deck-tile" href="practice.html?mode=deck&id=${deck.id}"><span class="deck-tile-title">${deck.title}</span><span class="deck-tile-sub">${deck.section}</span><span class="deck-tile-count">${deck.questions.length} questions</span></a>`).join("")}
        </div>
      </div>
    `;
  }

  function renderEmpty() {
    root.innerHTML = `
      <div class="page-head"><h2 style="margin:0">${setLabel}</h2></div>
      <div class="empty-state">Nothing here right now.</div>
      <div style="text-align:center"><a class="btn btn-secondary" href="practice.html">Back to practice</a></div>
    `;
  }

  function startTimer() {
    stopTimer();
    elapsedSec = 0;
    timerHandle = setInterval(() => {
      elapsedSec += 1;
      const el = document.getElementById("q-timer");
      if (el) el.textContent = fmt(elapsedSec);
    }, 1000);
  }
  function stopTimer() { if (timerHandle) { clearInterval(timerHandle); timerHandle = null; } }
  function fmt(sec) { const m = Math.floor(sec / 60); const s = sec % 60; return `${m}:${String(s).padStart(2, "0")}`; }

  function selfAccuracyOnTopic(topic, excludeQid) {
    const log = Store.load().answerLog.filter((a) => a.topic === topic && a.qid !== excludeQid);
    if (!log.length) return null;
    return Math.round((log.filter((a) => a.correct).length / log.length) * 100);
  }

  function renderPlayer() {
    if (idx >= queue.length) { renderSummary(); return; }
    answered = false;
    startedAt = Date.now();
    const q = queue[idx];
    const passage = q.passage || setPassage;
    const letters = ["A", "B", "C", "D"];
    const flagged = Store.isFlagged(q.id);
    const saved = Store.isSaved(q.id);

    root.innerHTML = `
      <div class="panel">
        <div class="player-toolbar">
          <div style="font-family:var(--font-heading);font-weight:800;font-size:13px">${setLabel}</div>
          <div class="text-muted" style="font-size:12px">Question ${idx + 1} of ${queue.length}</div>
          <div class="bar" style="flex:1"><span style="width:${(idx / queue.length) * 100}%"></span></div>
          <div style="display:flex;align-items:center;gap:6px;font-size:13px">${icon("clock", { size: 15 })}<span class="timer" id="q-timer">0:00</span></div>
          <button class="btn btn-secondary" id="flag-btn">${icon("flag", { size: 14 })}${flagged ? "Flagged" : "Flag"}</button>
          <button class="btn btn-secondary" id="save-btn">${icon("bookmark", { size: 14 })}${saved ? "Saved" : "Save"}</button>
        </div>
        <div class="player-grid">
          ${passage ? `
            <div class="player-passage">
              <div class="k" style="margin-bottom:10px">Passage</div>
              <div class="passage-block">${escapeHtml(passage)}</div>
            </div>` : ""}
          <div class="player-question" style="${passage ? "" : "grid-column:1 / -1;max-width:640px;margin:0 auto"}">
            <div style="display:flex;gap:8px;align-items:center;margin-bottom:12px">
              <span class="diff-tag level-${Data.difficultyOf(q)}">${Data.difficultyOf(q)}</span>
              ${q.topic ? `<span class="tag tag-neutral">${q.topic}</span>` : ""}
            </div>
            <p class="question-text">${escapeHtml(q.question)}</p>
            <div class="answer-options" id="options">
              ${q.options.map((opt, i) => `
                <button class="answer-option" data-i="${i}">
                  <span class="answer-letter">${letters[i]}.</span>
                  <span class="answer-option-text">${escapeHtml(opt)}</span>
                </button>`).join("")}
            </div>
            <div id="explain-slot"></div>
          </div>
        </div>
      </div>
    `;

    startTimer();

    document.getElementById("flag-btn").addEventListener("click", () => {
      const now = Store.toggleFlag(q.id);
      document.getElementById("flag-btn").innerHTML = `${icon("flag", { size: 14 })}${now ? "Flagged" : "Flag"}`;
    });
    document.getElementById("save-btn").addEventListener("click", () => {
      const now = Store.toggleSaved(q.id);
      document.getElementById("save-btn").innerHTML = `${icon("bookmark", { size: 14 })}${now ? "Saved" : "Save"}`;
    });

    document.querySelectorAll("#options .answer-option").forEach((btn) => {
      btn.addEventListener("click", () => selectOption(Number(btn.dataset.i), q));
    });
  }

  function selectOption(i, q) {
    if (answered) return;
    answered = true;
    stopTimer();
    const ms = Date.now() - startedAt;
    const wasCorrect = i === q.correct;
    if (wasCorrect) sessionCorrect += 1;

    Store.logAnswer({ qid: q.id, section: q.section, topic: q.topic, correct: wasCorrect, ms });

    const letters = ["A", "B", "C", "D"];
    document.querySelectorAll("#options .answer-option").forEach((btn, bi) => {
      btn.disabled = true;
      if (bi === q.correct) btn.classList.add("correct");
      else if (bi === i) btn.classList.add("wrong");
    });

    const selfAcc = selfAccuracyOnTopic(q.topic, q.id);
    const slot = document.getElementById("explain-slot");
    slot.innerHTML = `
      <div class="answer-explanation">
        <div style="display:flex;align-items:baseline;gap:12px;margin-bottom:8px;flex-wrap:wrap">
          <strong>${wasCorrect ? "Correct" : "Not quite"} — answer: ${letters[q.correct]}.</strong>
          ${selfAcc != null ? `<span class="tag tag-neutral">Your accuracy on ${q.topic}: ${selfAcc}%</span>` : ""}
        </div>
        <p>${escapeHtml(q.explanation)}</p>
      </div>
      <div class="review-row" id="grade-row"></div>
    `;
    renderGradeButtons(q.id, wasCorrect);
  }

  function renderGradeButtons(qid, wasCorrect) {
    const row = document.getElementById("grade-row");
    const grades = [
      { key: "again", label: "Again" }, { key: "hard", label: "Hard" },
      { key: "good", label: "Good" }, { key: "easy", label: "Easy" },
    ];
    row.innerHTML = grades.map((g) => `
      <button class="grade-btn review-${g.key} ${((g.key === "again" && !wasCorrect) || (g.key === "good" && wasCorrect)) ? "suggested" : ""}" data-key="${g.key}">${g.label}</button>
    `).join("");
    row.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => { Store.applyGrade(qid, btn.dataset.key); idx += 1; renderPlayer(); });
    });
  }

  function renderSummary() {
    root.innerHTML = `
      <div class="result-summary">
        <div class="k">${setLabel}</div>
        <div class="score"><span>${sessionCorrect}</span> / ${queue.length}</div>
        <p>Cards were rescheduled with spaced repetition — revisit due cards later to lock them in.</p>
        <div class="result-summary-actions">
          <a class="btn btn-primary" href="practice.html">Back to practice</a>
          <a class="btn btn-secondary" href="index.html">Dashboard</a>
        </div>
      </div>
    `;
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : s;
    return d.innerHTML;
  }

  const qlist = buildQueue();
  if (qlist === null) renderPicker();
  else if (!qlist.length) renderEmpty();
  else { queue = qlist; renderPlayer(); }
})();
