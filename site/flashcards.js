(function () {
  renderNav("flashcards");
  const root = document.getElementById("page-root");

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : s;
    return d.innerHTML;
  }

  function topicDecks() {
    const byTopic = {};
    Object.values(Data.allQuestions).forEach((q) => {
      const t = q.topic || q.section;
      byTopic[t] = byTopic[t] || [];
      byTopic[t].push(q);
    });
    return Object.entries(byTopic)
      .map(([topic, questions]) => ({ id: `topic:${topic}`, title: topic, questions }))
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
