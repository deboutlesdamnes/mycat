(function () {
  const store = Store.load();
  if (!store.profile.onboarded) {
    location.href = "onboarding.html";
    return;
  }

  renderNav("dashboard");

  const root = document.getElementById("page-root");
  const resetBtn = document.getElementById("reset-progress");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      if (confirm("Clear all progress, stats, and your study plan?")) {
        Store.reset();
        location.href = "onboarding.html";
      }
    });
  }

  const answerLog = store.answerLog;
  const composite = Stats.estimateComposite(answerLog, Data.SECTIONS);
  const delta14 = Stats.scoreDeltaOverDays(answerLog, Data.SECTIONS, 14);
  const pctl = Stats.approxPercentile(composite);

  const uniqueAnswered = new Set(answerLog.map((a) => a.qid)).size;
  const totalBank = Object.keys(Data.allQuestions).length;
  const overallCorrect = answerLog.filter((a) => a.correct).length;
  const overallAccuracy = answerLog.length ? Math.round((overallCorrect / answerLog.length) * 100) : null;

  const week = Stats.weeklyMinutes(store.activityLog);
  const weekHours = week.reduce((sum, d) => sum + d.minutes, 0) / 60;
  const maxMin = Math.max(1, ...week.map((d) => d.minutes));

  const secAcc = Stats.bySection(answerLog);
  const weakest = Stats.weakestTopics(answerLog, 5);
  const queue = Stats.adaptiveQueue(store, Data);

  const schedule = store.schedule;
  let nextExam = null;
  if (schedule) {
    const todayKey = Stats.dayKey(Date.now());
    nextExam = Object.entries(schedule.days)
      .filter(([k, tasks]) => k >= todayKey && tasks.some((t) => t.type === "exam"))
      .sort(([a], [b]) => (a < b ? -1 : 1))[0];
  }

  function scoreBlock() {
    if (composite == null) {
      return `
        <div class="stat-tile">
          <div class="k">Projected score</div>
          <p class="text-muted" style="margin-top:10px;font-size:13px">Answer a few more questions to get an estimate.</p>
        </div>`;
    }
    const target = store.profile.targetScore;
    const pct = Math.max(0, Math.min(100, ((composite - 472) / (528 - 472)) * 100));
    return `
      <div class="stat-tile">
        <div class="k">Projected score <span class="text-muted" style="text-transform:none;letter-spacing:0;font-weight:400">(estimated)</span></div>
        <div style="display:flex;align-items:flex-end;gap:12px;margin-top:10px">
          <div class="num" style="font-size:52px;color:var(--color-accent)">${composite}</div>
          <div style="font-size:13px;padding-bottom:8px">
            ${delta14 != null ? `<span style="color:${delta14 >= 0 ? "var(--color-correct)" : "var(--color-wrong)"};font-weight:600">${delta14 >= 0 ? "+" : ""}${delta14}</span> <span class="text-muted">last 14 days</span>` : `<span class="text-muted">~${pctl}th percentile (approx.)</span>`}
          </div>
        </div>
        <div class="bar" style="margin-top:14px"><span style="width:${pct}%"></span></div>
        <div style="display:flex;justify-content:space-between;font-size:11px;margin-top:6px" class="text-muted">
          <span>472</span><span>${target ? `Target ${target}` : "528"}</span>
        </div>
      </div>`;
  }

  function weekBlock() {
    return `
      <div class="stat-tile">
        <div class="k">This week</div>
        <div style="display:flex;align-items:flex-end;gap:8px;margin-top:10px">
          <div class="num" style="font-size:34px">${weekHours.toFixed(1)}</div>
          <div style="font-size:13px;padding-bottom:5px" class="text-muted">/ ${store.profile.weeklyHours || "—"} hrs goal</div>
        </div>
        <div class="chart-bars" style="margin-top:16px">
          ${week.map((d) => `<div style="height:${Math.max(6, (d.minutes / maxMin) * 100)}%" class="${d.isToday ? "today" : ""}" title="${d.label}: ${Math.round(d.minutes)} min"></div>`).join("")}
        </div>
        <div style="display:flex;justify-content:space-between;font-size:10px;margin-top:6px" class="text-muted">
          ${week.map((d) => `<span>${d.label}</span>`).join("")}
        </div>
      </div>`;
  }

  function bankBlock() {
    return `
      <div class="stat-tile">
        <div class="k">Question bank</div>
        <div style="display:flex;align-items:flex-end;gap:8px;margin-top:10px">
          <div class="num" style="font-size:34px">${uniqueAnswered}</div>
          <div style="font-size:13px;padding-bottom:5px" class="text-muted">answered</div>
        </div>
        <div class="row-list" style="margin-top:16px;border-top:1px solid var(--color-divider)">
          <div class="kv-row"><span>Accuracy</span><strong>${overallAccuracy != null ? overallAccuracy + "%" : "—"}</strong></div>
          <div class="kv-row"><span>Remaining</span><strong>${totalBank - uniqueAnswered} of ${totalBank}</strong></div>
        </div>
      </div>`;
  }

  function queueBlock() {
    return `
      <div>
        <div class="page-head" style="border-bottom:2px solid var(--color-divider);padding-bottom:10px">
          <h4 style="margin:0">Up next — adaptive queue</h4>
        </div>
        <div class="row-list">
          ${queue.map((item, i) => `
            <div class="row-item">
              <div class="row-num">${String(i + 1).padStart(2, "0")}</div>
              <div class="row-main">
                <div class="row-title">${item.title}</div>
                <div class="row-sub">${item.subtitle}</div>
              </div>
              <span class="tag ${item.tagClass}">${item.tag}</span>
              <a class="btn btn-primary" href="${item.href}">Start</a>
            </div>`).join("")}
        </div>
        ${nextExam ? `
          <div class="stat-grid" style="margin-top:24px;grid-template-columns:1fr auto">
            <div class="stat-tile">
              <div class="k">Next full-length</div>
              <div style="font-size:14px;font-weight:600;margin-top:6px">${new Date(nextExam[0]).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })}</div>
            </div>
            <div class="stat-tile" style="display:grid;place-items:center">
              <a class="btn btn-secondary" href="exams.html">View</a>
            </div>
          </div>` : ""}
      </div>`;
  }

  function sectionBlock() {
    const rows = Data.SECTIONS.map((s) => {
      const acc = Stats.accuracy(secAcc[s]);
      const score = Stats.estimateSectionScore(acc);
      const label = s.replace(" Foundations", "").replace(" of Biological Systems", "");
      return { label, acc, score };
    });
    return `
      <div>
        <div style="border-bottom:2px solid var(--color-divider);padding-bottom:10px"><h4 style="margin:0">Section performance</h4></div>
        <div style="padding:18px 0 6px">
          ${rows.map((r) => `
            <div style="margin-bottom:16px">
              <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:6px">
                <span>${r.label}</span><strong>${r.score != null ? r.score : "—"}</strong>
              </div>
              <div class="bar"><span style="width:${r.acc != null ? Math.round(r.acc * 100) : 0}%"></span></div>
            </div>`).join("")}
        </div>
        <div style="border-bottom:2px solid var(--color-divider);padding-bottom:10px;margin-top:24px"><h4 style="margin:0">Weakest topics</h4></div>
        ${weakest.length ? `
          <table class="table"><tbody>
            ${weakest.map((w) => `<tr><td>${w.topic}</td><td style="text-align:right;width:60px" class="text-muted">${Math.round(w.accuracy * 100)}%</td></tr>`).join("")}
          </tbody></table>` : `<p class="text-muted" style="font-size:13px">Answer a few more questions in each topic to see this.</p>`}
      </div>`;
  }

  root.innerHTML = `
    <div class="page-head">
      <h2 style="margin:0">Dashboard</h2>
    </div>
    <div class="stat-grid" style="grid-template-columns:repeat(3, minmax(220px, 1fr))">
      ${scoreBlock()}
      ${weekBlock()}
      ${bankBlock()}
    </div>
    <div class="cols-2">
      ${queueBlock()}
      ${sectionBlock()}
    </div>
  `;
})();
