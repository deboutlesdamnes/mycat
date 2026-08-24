// Injects the shared top nav into <div id="nav-root"></div>, present on
// every new page, so the markup isn't duplicated across HTML files.
function renderNav(active) {
  const root = document.getElementById("nav-root");
  if (!root) return;

  const links = [
    { href: "index.html", label: "Dashboard", key: "dashboard" },
    { href: "practice.html", label: "Practice", key: "practice" },
    { href: "flashcards.html", label: "Flashcards", key: "flashcards" },
    { href: "exams.html", label: "Exams", key: "exams" },
    { href: "schedule.html", label: "Schedule", key: "schedule" },
  ];

  const s = Store.load();
  const streak = Stats.streak(s.activityLog);

  root.innerHTML = `
    <div class="nav2">
      <a class="nav2-brand" href="index.html">
        <span aria-hidden="true">🩺</span> MyCat
      </a>
      <div class="nav2-links">
        ${links.map((l) => `<a href="${l.href}" ${l.key === active ? 'aria-current="page"' : ""}>${l.label}</a>`).join("")}
      </div>
      ${streak > 0 ? `<div class="nav2-streak">${icon("flame", { size: 15 })}${streak}-day streak</div>` : ""}
      <div class="nav2-avatar" title="MyCat">🩺</div>
    </div>
  `;
}
