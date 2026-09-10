(function () {
  renderNav("exams");
  const root = document.getElementById("page-root");
  const store0 = Store.load();

  const REASONS = [
    { key: "content", label: "Content gap" },
    { key: "misread", label: "Misread the question" },
    { key: "time", label: "Time pressure" },
    { key: "careless", label: "Careless" },
  ];

  function sectionSeconds(section) {
    return /Critical Analysis/i.test(section) ? 90 * 60 : 95 * 60;
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : s;
    return d.innerHTML;
  }

  // ---------------- list view ----------------
  function renderList() {
    const store = Store.load();
    const sittings = store.testAttempts.filter((a) => a.kind === "sitting").slice().reverse();

    root.innerHTML = `
      <div class="page-head">
        <h2 style="margin:0">Exams</h2>
        <button class="btn btn-primary" id="start-exam">Start full exam day</button>
      </div>
      ${sittings.length ? `
        <div class="panel panel-pad">
          <div class="row-list">
            ${sittings.map((a) => `
              <div class="row-item">
                <div class="row-main">
                  <div class="row-title">Full-length · ${new Date(a.date).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}</div>
                  <div class="row-sub">${a.correct} / ${a.total} correct</div>
                </div>
                <div class="num" style="font-size:22px;color:var(--color-accent)">${a.compositeScore}</div>
                <a class="btn btn-secondary" href="exams.html?attempt=${a.date}">View report</a>
              </div>`).join("")}
          </div>
        </div>` : `<div class="empty-state">No full-length attempts yet. A full exam day runs all four sections back to back with real per-section timers.</div>`}
    `;
    document.getElementById("start-exam").addEventListener("click", runExam);
  }

  // ---------------- running an exam ----------------
  function runExam() {
    const sections = Data.fullDecks; // [{id,title,section,questions}]
    let si = 0, qi = 0, secondsLeft = 0, timerHandle = null;
    const results = sections.map((d) => ({ deckId: d.id, section: d.section, correct: 0, total: d.questions.length, missedIds: [], perQuestionMs: [] }));
    let qStartedAt = 0;

    function startSection() {
      secondsLeft = sectionSeconds(sections[si].section);
      qi = 0;
      renderQuestion();
      clearInterval(timerHandle);
      timerHandle = setInterval(() => {
        secondsLeft -= 1;
        const el = document.getElementById("exam-timer");
        if (el) el.textContent = fmt(secondsLeft);
        if (secondsLeft <= 0) { clearInterval(timerHandle); nextSection(); }
      }, 1000);
    }

    function fmt(sec) { sec = Math.max(0, sec); const m = Math.floor(sec / 60); const s = sec % 60; return `${m}:${String(s).padStart(2, "0")}`; }

    function renderQuestion() {
      const deck = sections[si];
      const q = deck.questions[qi];
      qStartedAt = Date.now();
      const letters = ["A", "B", "C", "D"];
      const kc = Glossary.keyConcepts(q);
      const fig = Glossary.figureHTML(q);
      root.innerHTML = `
        <div class="panel player-panel">
          <div class="player-toolbar">
            <div class="player-title">${deck.title}</div>
            <div class="player-progress">
              <div class="player-count text-muted">Question ${qi + 1} of ${deck.questions.length} · Section ${si + 1} of ${sections.length}</div>
              <div class="bar"><span style="width:${(qi / deck.questions.length) * 100}%"></span></div>
            </div>
            <div class="player-timer">${icon("clock", { size: 15 })}<span class="timer" id="exam-timer">${fmt(secondsLeft)}</span></div>
          </div>
          <div class="player-grid">
            ${q.passage ? `<div class="player-passage"><div class="k">Passage</div><div class="passage-scroll"><div class="passage-block">${Glossary.linkify(q.passage, { limit: 3 })}</div>${fig}</div></div>` : ""}
            <div class="player-question" style="${q.passage ? "" : "grid-column:1 / -1;max-width:640px;margin:0 auto"}">
              <p class="question-text">${Glossary.linkify(q.question, { terms: kc.terms, limit: 2 })}</p>
              ${q.passage ? "" : fig}
              <div class="answer-options" id="options">
                ${q.options.map((opt, i) => `<button class="answer-option" data-i="${i}"><span class="answer-letter">${letters[i]}.</span><span class="answer-option-text">${Glossary.linkify(opt, { terms: kc.terms, limit: 3 })}</span></button>`).join("")}
              </div>
            </div>
          </div>
        </div>
      `;
      document.querySelectorAll("#options .answer-option").forEach((btn) => {
        btn.addEventListener("click", () => selectAnswer(Number(btn.dataset.i), q));
      });
    }

    function selectAnswer(i, q) {
      document.querySelectorAll("#options .answer-option").forEach((b) => (b.disabled = true));
      const ms = Date.now() - qStartedAt;
      const wasCorrect = i === q.correct;
      const r = results[si];
      r.perQuestionMs.push(ms);
      if (wasCorrect) r.correct += 1; else r.missedIds.push(q.id || `${sections[si].id}-${qi}`);
      Store.logAnswer({ qid: q.id || `${sections[si].id}-${qi}`, section: q.section, topic: q.topic, correct: wasCorrect, ms });
      qi += 1;
      if (qi >= sections[si].questions.length) { clearInterval(timerHandle); nextSection(); }
      else setTimeout(renderQuestion, 200);
    }

    function nextSection() {
      si += 1;
      if (si >= sections.length) { finishExam(); return; }
      startSection();
    }

    function finishExam() {
      const totalCorrect = results.reduce((s, r) => s + r.correct, 0);
      const totalQ = results.reduce((s, r) => s + r.total, 0);
      const secAcc = {};
      results.forEach((r) => { secAcc[r.section] = { correct: r.correct, total: r.total }; });
      const sectionScores = Data.SECTIONS.map((s) => {
        const acc = Stats.accuracy(secAcc[s]);
        return { section: s, score: Stats.estimateSectionScore(acc) || 125, correct: (secAcc[s] || {}).correct || 0, total: (secAcc[s] || {}).total || 0 };
      });
      const compositeScore = sectionScores.reduce((s, x) => s + x.score, 0);
      const attempt = {
        kind: "sitting", correct: totalCorrect, total: totalQ,
        sectionScores, compositeScore,
        missedIds: results.flatMap((r) => r.missedIds),
        perQuestionMs: results.flatMap((r) => r.perQuestionMs),
        missedReasons: {},
      };
      Store.addTestAttempt(attempt);
      const saved = Store.load();
      const justAdded = saved.testAttempts[saved.testAttempts.length - 1];
      renderTagging(justAdded);
    }

    startSection();
  }

  // ---------------- tag missed reasons ----------------
  function renderTagging(attempt) {
    const missed = attempt.missedIds.map((id) => Data.allQuestions[id]).filter(Boolean);
    if (!missed.length) { renderReport(attempt.date); return; }

    root.innerHTML = `
      <div class="page-head"><h2 style="margin:0">Quick review — why'd you miss these?</h2></div>
      <p class="text-muted">Optional, but it makes "where the points went" on your report real instead of a guess.</p>
      <div class="panel panel-pad">
        <div class="row-list" id="missed-list">
          ${missed.map((q) => `
            <div class="row-item" data-qid="${q.id}">
              <div class="row-main">
                <div class="row-title">${escapeHtml(q.question).slice(0, 90)}${q.question.length > 90 ? "…" : ""}</div>
                <div class="tag-chip-row">
                  ${REASONS.map((r) => `<button class="tag-chip" data-reason="${r.key}">${r.label}</button>`).join("")}
                </div>
              </div>
            </div>`).join("")}
        </div>
      </div>
      <div style="text-align:right"><button class="btn btn-primary" id="continue-btn">Continue to report ${icon("arrow-right", { size: 14 })}</button></div>
    `;
    document.querySelectorAll("#missed-list .row-item").forEach((row) => {
      const qid = row.dataset.qid;
      row.querySelectorAll(".tag-chip").forEach((chip) => {
        chip.addEventListener("click", () => {
          row.querySelectorAll(".tag-chip").forEach((c) => c.classList.remove("selected"));
          chip.classList.add("selected");
          Store.tagMissedReason(attempt.date, qid, chip.dataset.reason);
        });
      });
    });
    document.getElementById("continue-btn").addEventListener("click", () => renderReport(attempt.date));
  }

  // ---------------- report ----------------
  function renderReport(attemptDate) {
    const store = Store.load();
    const sittings = store.testAttempts.filter((a) => a.kind === "sitting");
    const idxInList = sittings.findIndex((a) => a.date === Number(attemptDate));
    const attempt = sittings[idxInList];
    if (!attempt) { renderList(); return; }
    const prev = sittings[idxInList - 1];

    const pctl = Stats.approxPercentile(attempt.compositeScore);
    const secondsUsed = attempt.perQuestionMs ? Math.round(attempt.perQuestionMs.reduce((a, b) => a + b, 0) / 1000) : null;

    const reasonCounts = {};
    REASONS.forEach((r) => (reasonCounts[r.key] = 0));
    let untagged = 0;
    (attempt.missedIds || []).forEach((qid) => {
      const reason = (attempt.missedReasons || {})[qid];
      if (reason && reasonCounts[reason] != null) reasonCounts[reason] += 1;
      else untagged += 1;
    });

    const pacing = bucketPacing(attempt.perQuestionMs || [], 8);
    const maxPace = Math.max(1, ...pacing);

    const worstSection = attempt.sectionScores.slice().sort((a, b) => a.score - b.score)[0];

    root.innerHTML = `
      <div class="page-head">
        <h2 style="margin:0">Exam review</h2>
        <a class="btn btn-secondary" href="exams.html">All attempts</a>
      </div>
      <div class="panel">
        <div class="score-hero-row">
          <div class="score-hero">
            <div class="k">Full-length · ${new Date(attempt.date).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}</div>
            <div class="score-num-lg">${attempt.compositeScore}</div>
            <div style="font-size:14px;opacity:.9">~${pctl}th percentile (approx.)${prev ? ` · <strong>${attempt.compositeScore - prev.compositeScore >= 0 ? "+" : ""}${attempt.compositeScore - prev.compositeScore}</strong> from last sitting` : ""}</div>
            <div style="font-size:13px;opacity:.85;margin-top:4px">Confidence band ${attempt.compositeScore - 2}–${attempt.compositeScore + 2}</div>
            <hr class="hr" style="background:rgba(255,255,255,.35)">
            <div class="kv-row" style="border-color:rgba(255,255,255,.2)"><span style="opacity:.8">Target</span><strong>${store.profile.targetScore || "—"}</strong></div>
            <div class="kv-row" style="border-color:rgba(255,255,255,.2)"><span style="opacity:.8">Gap</span><strong>${store.profile.targetScore ? Math.max(0, store.profile.targetScore - attempt.compositeScore) : "—"}</strong></div>
          </div>
          <div class="score-detail">
            <h4>Section scores</h4>
            <table class="table score-table">
              <thead><tr><th>Section</th><th style="text-align:right">Score</th><th style="text-align:right">Correct</th><th class="col-acc" style="width:36%">Accuracy</th></tr></thead>
              <tbody>
                ${attempt.sectionScores.map((s) => `
                  <tr>
                    <td>${s.section}</td>
                    <td style="text-align:right"><strong>${s.score}</strong> <span class="text-muted" style="font-weight:400;font-size:12px">±1</span></td>
                    <td style="text-align:right" class="text-muted">${s.correct}/${s.total}</td>
                    <td class="col-acc"><div class="bar"><span style="width:${s.total ? Math.round((s.correct / s.total) * 100) : 0}%"></span></div></td>
                  </tr>`).join("")}
              </tbody>
            </table>
            <p class="text-muted" style="font-size:12px;margin-top:8px">Confidence bands: total ±2 · section ±1.</p>
          </div>
        </div>
        <div class="report-cols">
          <div class="report-col">
            <h4>Where the points went</h4>
            <div class="row-list" style="border-top:2px solid var(--color-divider);margin-top:12px">
              <div class="kv-row"><span>Correct</span><strong>${attempt.correct} / ${attempt.total}</strong></div>
              ${REASONS.map((r) => `<div class="kv-row"><span>${r.label}</span><strong>${reasonCounts[r.key]}</strong></div>`).join("")}
              ${untagged ? `<div class="kv-row"><span>Untagged misses</span><strong>${untagged}</strong></div>` : ""}
            </div>
          </div>
          <div class="report-col">
            <h4>Pacing</h4>
            <div class="chart-bars" style="height:120px;margin-top:20px">
              ${pacing.map((v) => `<div style="height:${Math.max(4, (v / maxPace) * 100)}%"></div>`).join("")}
            </div>
            <div style="display:flex;justify-content:space-between;font-size:10px;margin-top:6px" class="text-muted"><span>Q1</span><span>Q${attempt.total}</span></div>
            <p class="text-muted" style="font-size:13px;margin-top:16px">${secondsUsed != null ? `Average ${Math.round(secondsUsed / attempt.total)}s per question across the exam.` : ""}</p>
          </div>
          <div class="report-col">
            <h4>Recommended next</h4>
            <div class="row-list" style="border-top:2px solid var(--color-divider);margin-top:12px">
              <a class="row-item" href="practice.html?mode=section&section=${encodeURIComponent(worstSection.section)}" style="text-decoration:none;color:inherit">
                <div class="row-main"><div class="row-title">Practice · ${worstSection.section.replace(" Foundations", "")}</div><div class="row-sub">Lowest-scoring section this sitting</div></div>
                ${icon("chevron-right", { size: 16, className: "text-muted" })}
              </a>
              <a class="row-item" href="practice.html?mode=missed" style="text-decoration:none;color:inherit">
                <div class="row-main"><div class="row-title">Review ${attempt.missedIds.length} missed questions</div><div class="row-sub">Grouped by topic in practice</div></div>
                ${icon("chevron-right", { size: 16, className: "text-muted" })}
              </a>
            </div>
            <a class="btn btn-primary btn-block" href="schedule.html">Apply to my plan ${icon("arrow-right", { size: 14, className: "icon-push-end" })}</a>
          </div>
        </div>
      </div>
    `;
  }

  function bucketPacing(msArray, n) {
    if (!msArray.length) return new Array(n).fill(0);
    const out = [];
    const size = Math.ceil(msArray.length / n);
    for (let i = 0; i < n; i++) {
      const chunk = msArray.slice(i * size, (i + 1) * size);
      if (!chunk.length) { out.push(0); continue; }
      out.push(chunk.reduce((a, b) => a + b, 0) / chunk.length);
    }
    return out;
  }

  const params = new URLSearchParams(location.search);
  const attemptParam = params.get("attempt");
  if (attemptParam) renderReport(attemptParam);
  else renderList();
})();
