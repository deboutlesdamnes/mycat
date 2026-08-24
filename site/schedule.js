(function () {
  renderNav("schedule");
  const root = document.getElementById("page-root");
  const store = Store.load();

  let schedule = store.schedule;
  if (!schedule && store.profile.testDate) {
    schedule = Stats.generateSchedule(store.profile, Data, store.testAttempts);
    Store.setSchedule(schedule);
  }

  const today = new Date(); today.setHours(0, 0, 0, 0);
  let viewMonth = today.getMonth();
  let viewYear = today.getFullYear();
  let selected = Stats.dayKey(today.getTime());

  const TASK_CLASS = { practice: "", review: "review", cars: "review", exam: "exam", rest: "review" };
  const TASK_LABEL_CLASS = { exam: "exam", rest: "review" };

  function render() {
    if (!schedule) {
      root.innerHTML = `
        <div class="page-head"><h2 style="margin:0">Schedule</h2></div>
        <div class="panel panel-pad">
          <p>Set a test date to generate a study schedule.</p>
          <a class="btn btn-primary" href="onboarding.html">Set up your plan</a>
        </div>`;
      return;
    }

    const monthName = new Date(viewYear, viewMonth, 1).toLocaleDateString(undefined, { month: "long", year: "numeric" });
    root.innerHTML = `
      <div class="page-head"><h2 style="margin:0">Schedule</h2></div>
      <div class="panel">
        <div class="cal-toolbar">
          <h3 style="margin:0">${monthName}</h3>
          <div style="display:flex;gap:2px">
            <button class="btn btn-secondary btn-icon" id="prev-month">${icon("chevron-left", { size: 16 })}</button>
            <button class="btn btn-secondary btn-icon" id="next-month">${icon("chevron-right", { size: 16 })}</button>
          </div>
          <div class="cal-legend">
            <div class="cal-legend-item"><span class="cal-legend-dot" style="background:var(--color-accent)"></span>Practice</div>
            <div class="cal-legend-item"><span class="cal-legend-dot" style="background:var(--color-accent-300)"></span>Content review</div>
            <div class="cal-legend-item"><span class="cal-legend-dot" style="background:var(--color-text)"></span>Full-length</div>
          </div>
          <a class="btn btn-secondary" href="onboarding.html">Edit availability</a>
          <button class="btn btn-primary" id="rebalance">Rebalance plan</button>
        </div>
        <div class="cal-body">
          <div>
            <div class="cal-dow">
              ${["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) => `<div class="k" style="padding:10px 12px">${d}</div>`).join("")}
            </div>
            <div class="cal-grid" id="cal-grid"></div>
          </div>
          <div class="cal-side" id="cal-side"></div>
        </div>
      </div>
    `;

    document.getElementById("prev-month").addEventListener("click", () => { viewMonth -= 1; if (viewMonth < 0) { viewMonth = 11; viewYear -= 1; } renderGrid(); });
    document.getElementById("next-month").addEventListener("click", () => { viewMonth += 1; if (viewMonth > 11) { viewMonth = 0; viewYear += 1; } renderGrid(); });
    document.getElementById("rebalance").addEventListener("click", () => {
      schedule = Stats.generateSchedule(store.profile, Data, store.testAttempts);
      Store.setSchedule(schedule);
      renderGrid();
    });

    renderGrid();
  }

  function renderGrid() {
    const grid = document.getElementById("cal-grid");
    const first = new Date(viewYear, viewMonth, 1);
    const startOffset = (first.getDay() + 6) % 7; // 0=Mon
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
    const cells = [];
    for (let i = 0; i < startOffset; i++) {
      const d = new Date(viewYear, viewMonth, 1 - (startOffset - i));
      cells.push({ date: d, otherMonth: true });
    }
    for (let d = 1; d <= daysInMonth; d++) cells.push({ date: new Date(viewYear, viewMonth, d), otherMonth: false });
    while (cells.length % 7 !== 0 || cells.length < 35) {
      const last = cells[cells.length - 1].date;
      cells.push({ date: new Date(last.getFullYear(), last.getMonth(), last.getDate() + 1), otherMonth: true });
    }

    grid.innerHTML = cells.map((c) => {
      const key = Stats.dayKey(c.date.getTime());
      const tasks = (schedule.days[key] || []);
      const isToday = key === Stats.dayKey(today.getTime());
      return `
        <div class="cal-day ${c.otherMonth ? "other-month" : ""} ${isToday ? "today" : ""} ${key === selected ? "selected" : ""}" data-key="${key}">
          <div class="num" style="font-size:12px">${c.date.getDate()}${isToday ? " · Today" : ""}</div>
          ${tasks.map((t) => `<div class="cal-task ${TASK_LABEL_CLASS[t.type] || ""}">${t.label}</div>`).join("")}
        </div>`;
    }).join("");

    grid.querySelectorAll(".cal-day").forEach((el) => {
      el.addEventListener("click", () => { selected = el.dataset.key; renderGrid(); renderSide(); });
    });

    renderSide();
  }

  function renderSide() {
    const side = document.getElementById("cal-side");
    const tasks = schedule.days[selected] || [];
    const d = new Date(selected + "T00:00:00");
    const label = d.toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });
    const totalMinutes = tasks.filter((t) => t.type !== "rest").length * 60;

    side.innerHTML = `
      <div class="k">${label}</div>
      <h4 style="margin-top:8px">${tasks.length ? `Plan · ~${Math.round(totalMinutes / 60)} hr` : "Nothing scheduled"}</h4>
      <div class="row-list" style="margin-top:14px;border-top:2px solid var(--color-divider)">
        ${tasks.map((t) => `
          <div class="row-item">
            <div class="row-main">
              <div class="row-title">${t.label}</div>
            </div>
            ${t.type === "exam" ? '<span class="tag tag-accent">Exam</span>' : ""}
          </div>`).join("")}
      </div>
      ${tasks.some((t) => t.type !== "rest") ? `<a class="btn btn-primary btn-block" href="practice.html">Start today's plan ${icon("arrow-right", { size: 14, className: "icon-push-end" })}</a>` : ""}
    `;
  }

  render();
})();
