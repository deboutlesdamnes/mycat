// Injects the shared top nav into <div id="nav-root"></div>, present on
// every new page, so the markup isn't duplicated across HTML files.
// Structure matches the mockup: brand, then the links, then streak/avatar,
// relying on .nav-brand's margin-right:auto to push everything else to the
// right as a group. The links sit in a `display: contents` wrapper so they
// lay out as flat children of .nav on wide screens and become their own
// tab-strip row on phones.
let _navActive = null;

function renderNav(active) {
  _navActive = active;
  const root = document.getElementById("nav-root");
  if (!root) return;

  const links = [
    { href: "index.html", label: "Dashboard", key: "dashboard", icon: "layout-dashboard" },
    { href: "practice.html", label: "Practice", key: "practice", icon: "pencil" },
    { href: "flashcards.html", label: "Flashcards", key: "flashcards", icon: "layers" },
    { href: "exams.html", label: "Exams", key: "exams", icon: "clipboard-check" },
    { href: "schedule.html", label: "Schedule", key: "schedule", icon: "calendar" },
  ];

  const s = Store.load();
  const streak = Stats.streak(s.activityLog);
  const dark = effectiveTheme() === "dark";

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
      <div class="nav-brand">${mycatMark(36)}<span style="letter-spacing:-.01em">my<span style="color:var(--color-accent)">cat</span></span></div>
      <nav class="nav-links">${links.map((l) => `<a href="${l.href}" ${l.key === active ? 'aria-current="page"' : ""}><span class="nav-icon">${icon(l.icon, { size: 26 })}</span><span class="nav-label">${l.label}</span></a>`).join("")}</nav>
      ${streak > 0 ? `<div class="nav-streak" title="${streak}-day streak">${icon("flame", { size: 15 })}<span>${streak}<span class="nav-streak-label">-day streak</span></span></div>` : ""}
      <button class="nav-theme" id="theme-toggle" type="button" aria-label="Switch to ${dark ? "light" : "dark"} mode" title="Switch to ${dark ? "light" : "dark"} mode">${icon(dark ? "sun" : "moon", { size: 17 })}</button>
      ${acctHtml}
    </div>
  `;

  document.getElementById("theme-toggle").addEventListener("click", () => {
    const next = effectiveTheme() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem(THEME_KEY, next); } catch (e) {}
    renderNav(_navActive);
  });

  measureNav(root);
}

// Theme: follows the OS until the toggle stores an explicit choice. Each
// page's <head> applies the stored choice before first paint.
const THEME_KEY = "mycat_theme";
const _darkQuery = window.matchMedia ? matchMedia("(prefers-color-scheme: dark)") : null;
function effectiveTheme() {
  const t = document.documentElement.dataset.theme;
  if (t === "light" || t === "dark") return t;
  return _darkQuery && _darkQuery.matches ? "dark" : "light";
}
// Keep the toggle's icon right if the OS theme flips while the page is open.
if (_darkQuery && _darkQuery.addEventListener) {
  _darkQuery.addEventListener("change", () => {
    if (document.getElementById("nav-root")) renderNav(_navActive);
  });
}

// Publishes the nav's height as --nav-h so pages that need to fill the rest of
// the viewport (the practice/exam player) can size themselves against it —
// the nav wraps to two rows on narrow screens, so it isn't a fixed number.
let _navObserver = null;
function measureNav(root) {
  const nav = root.querySelector(".nav");
  if (!nav) return;
  const publish = () => document.documentElement.style.setProperty("--nav-h", `${nav.offsetHeight}px`);
  publish();
  if (typeof ResizeObserver !== "undefined") {
    if (_navObserver) _navObserver.disconnect();
    _navObserver = new ResizeObserver(publish);
    _navObserver.observe(nav);
  }
}

// Re-render the nav when auth state changes (sign in / out / session restore).
if (typeof Auth !== "undefined" && Auth.onChange) {
  Auth.onChange(() => {
    if (document.getElementById("nav-root")) renderNav(_navActive);
  });
}
