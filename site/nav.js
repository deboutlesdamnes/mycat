// Injects the shared top nav into <div id="nav-root"></div>, present on
// every new page, so the markup isn't duplicated across HTML files.
// Structure matches the mockup exactly: flat children of .nav (brand, then
// bare <a> links, then streak/avatar), relying on .nav-brand's
// margin-right:auto to push everything else to the right as a group.
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
    <div class="nav">
      <div class="nav-brand"><span aria-hidden="true">🩺</span>MyCat</div>
      ${links.map((l) => `<a href="${l.href}" ${l.key === active ? 'aria-current="page"' : ""}>${l.label}</a>`).join("")}
      ${streak > 0 ? `<div class="nav-streak">${icon("flame", { size: 15 })}${streak}-day streak</div>` : ""}
      <div class="nav-avatar" title="MyCat">🩺</div>
    </div>
  `;
}
