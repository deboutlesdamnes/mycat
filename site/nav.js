// Injects the shared top nav into <div id="nav-root"></div>, present on
// every new page, so the markup isn't duplicated across HTML files.
// Structure matches the mockup exactly: flat children of .nav (brand, then
// bare <a> links, then streak/avatar), relying on .nav-brand's
// margin-right:auto to push everything else to the right as a group.
let _navActive = null;

function renderNav(active) {
  _navActive = active;
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

  const authOn = typeof Auth !== "undefined" && Auth.enabled;
  const signedIn = authOn && (Auth.user() || Auth.hasStoredSession());
  let acctHtml;
  if (authOn && signedIn) {
    const email = Auth.email() || "";
    const initial = (email.trim()[0] || "🩺").toUpperCase();
    acctHtml = `<a href="account.html" class="nav-account" ${active === "account" ? 'aria-current="page"' : ""} title="${email || "Account"}"><span class="nav-avatar">${initial}</span></a>`;
  } else if (authOn) {
    acctHtml = `<a href="account.html" class="nav-account-link" ${active === "account" ? 'aria-current="page"' : ""}>Log in</a>`;
  } else {
    acctHtml = `<a href="account.html" class="nav-account" ${active === "account" ? 'aria-current="page"' : ""} title="Account"><span class="nav-avatar">🩺</span></a>`;
  }

  root.innerHTML = `
    <div class="nav">
      <div class="nav-brand"><span aria-hidden="true">🩺</span>MyCat</div>
      ${links.map((l) => `<a href="${l.href}" ${l.key === active ? 'aria-current="page"' : ""}>${l.label}</a>`).join("")}
      ${streak > 0 ? `<div class="nav-streak">${icon("flame", { size: 15 })}${streak}-day streak</div>` : ""}
      ${acctHtml}
    </div>
  `;
}

// Re-render the nav when auth state changes (sign in / out / session restore).
if (typeof Auth !== "undefined" && Auth.onChange) {
  Auth.onChange(() => {
    if (document.getElementById("nav-root")) renderNav(_navActive);
  });
}
