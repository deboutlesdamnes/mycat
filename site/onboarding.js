(function () {
  renderNav(null);

  const root = document.getElementById("page-root");
  const store = Store.load();
  const totalBank = Object.keys(Data.allQuestions).length;
  const uniqueAnswered = new Set(store.answerLog.map((a) => a.qid)).size;
  const sittingsDone = store.testAttempts.filter((a) => a.kind === "sitting").length;
  const examsRemaining = Math.max(0, Data.fullDecks.length ? 4 - sittingsDone : 0);

  const lastSitting = [...store.testAttempts].reverse().find((a) => a.kind === "sitting");
  const autoBaseline = lastSitting ? lastSitting.compositeScore : null;

  function weeksAway(dateStr) {
    if (!dateStr) return null;
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return null;
    const ms = d.getTime() - Date.now();
    return Math.max(0, Math.round(ms / (7 * 24 * 60 * 60 * 1000)));
  }

  function render() {
    const p = store.profile;
    const weeks = weeksAway(p.testDate);

    root.innerHTML = `
      <div class="panel" style="max-width:1000px;margin:0 auto;width:100%">
        <div class="onboard-grid">
          <div class="onboard-main">
            <div class="k" style="margin-bottom:8px">Set up your plan</div>
            <h1 class="onboard-title">${autoBaseline ? `Your baseline is a ${autoBaseline}.` : "Let's set your target."}</h1>
            <p class="text-muted" style="max-width:56ch">
              ${autoBaseline
                ? "Based on your most recent full-length sitting. Set a target score and test date and we'll build your study plan around it."
                : "No full-length attempt yet — enter a baseline if you know one (a past AAMC or MyCat full-length score), or leave it blank and we'll estimate it as you practice."}
            </p>
            <hr class="hr">

            <form id="onboard-form">
              <div class="form-grid" style="margin-bottom:20px">
                <div class="field">
                  <label>Baseline score ${autoBaseline ? "(from your last sitting)" : "(optional)"}</label>
                  <input class="input" type="number" min="472" max="528" id="f-baseline" value="${p.baselineScore || autoBaseline || ""}" ${autoBaseline ? "readonly" : ""} placeholder="e.g. 502">
                </div>
                <div class="field">
                  <label>Target score</label>
                  <input class="input" type="number" min="472" max="528" id="f-target" value="${p.targetScore || ""}" required placeholder="e.g. 515">
                </div>
              </div>

              <div class="form-grid" style="column-gap:28px">
                <div class="field">
                  <label>Test date</label>
                  <input class="input" type="date" id="f-date" value="${p.testDate || ""}" required>
                  <div class="text-muted" style="font-size:11px;margin-top:6px" id="weeks-away">${weeks != null ? `${weeks} weeks away` : ""}</div>
                </div>
                <div class="field">
                  <label>Weekly study hours</label>
                  <div class="seg" style="width:100%">
                    ${["5-10", "10-15", "15-20", "20+"].map((label, i) => {
                      const mid = [7, 12, 17, 22][i];
                      const checked = p.weeklyHours ? p.weeklyHours === mid : i === 1;
                      return `<label class="seg-opt" style="flex:1;justify-content:center"><input type="radio" name="hrs" value="${mid}" ${checked ? "checked" : ""}>${label}</label>`;
                    }).join("")}
                  </div>
                </div>
              </div>
              <button type="submit" class="btn btn-primary btn-block" style="margin-top:28px">Build my study plan ${icon("arrow-right", { size: 15, className: "icon-push-end" })}</button>
            </form>
          </div>

          <div class="onboard-side">
            <div class="k" style="margin-bottom:16px">Your plan</div>
            <div class="row-list" style="border-top:2px solid var(--color-divider)">
              <div class="kv-row"><span>Study weeks</span><strong>${weeks != null ? weeks : "—"}</strong></div>
              <div class="kv-row"><span>Practice questions</span><strong>${totalBank - uniqueAnswered}</strong></div>
              <div class="kv-row"><span>Full-length exams</span><strong>${examsRemaining}</strong></div>
              <div class="kv-row"><span>Weak-area drills</span><strong>Adaptive</strong></div>
            </div>
            <div class="callout" style="margin-top:24px">
              <div class="k">How this works</div>
              <p>Your plan updates from real practice data as you go — projected score, weakest topics, and the daily queue all come from your own answers, not a generic script.</p>
            </div>
          </div>
        </div>
      </div>
    `;

    document.getElementById("f-date").addEventListener("input", (e) => {
      const w = weeksAway(e.target.value);
      document.getElementById("weeks-away").textContent = w != null ? `${w} weeks away` : "";
    });

    document.getElementById("onboard-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const baseline = document.getElementById("f-baseline").value;
      const target = document.getElementById("f-target").value;
      const testDate = document.getElementById("f-date").value;
      const hrs = document.querySelector('input[name="hrs"]:checked');
      Store.setProfile({
        onboarded: true,
        baselineScore: baseline ? Number(baseline) : autoBaseline,
        targetScore: Number(target),
        testDate,
        weeklyHours: hrs ? Number(hrs.value) : 12,
      });
      location.href = "index.html";
    });
  }

  render();
})();
