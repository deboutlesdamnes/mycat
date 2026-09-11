// Small inline-SVG icon set (original glyphs, not a third-party asset) so the
// site makes zero external network requests.
const ICON_PATHS = {
  calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
  flame: '<path d="M12 2c1 3-3 4-3 7a3 3 0 0 0 6 0c0-1-.5-2-1-2.5.7 2 0 3.5-1.5 4.5-2 1.3-3.5 3.3-3.5 5.5a5 5 0 0 0 10 0c0-5-4-6-7-14.5Z"/>',
  "chevron-left": '<polyline points="15 18 9 12 15 6"/>',
  "chevron-right": '<polyline points="9 18 15 12 9 6"/>',
  "arrow-right": '<line x1="4" y1="12" x2="20" y2="12"/><polyline points="14 6 20 12 14 18"/>',
  check: '<polyline points="20 6 9 17 4 12"/>',
  x: '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
  flag: '<path d="M4 3v18"/><path d="M4 4h11l-2 4 2 4H4"/>',
  clock: '<circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 16 14"/>',
  bookmark: '<path d="M6 3h12v18l-6-4-6 4V3Z"/>',
  download: '<path d="M12 3v12"/><polyline points="7 10 12 15 17 10"/><path d="M5 21h14"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/>',
  plus: '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
  pencil: '<path d="M17 3a2.83 2.83 0 1 1 4 4L7 21l-4 1 1-4Z"/>',
  "clipboard-check": '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><polyline points="9 14 11 16 15 12"/>',
  layers: '<polygon points="12 3 21 8 12 13 3 8 12 3"/><polyline points="3 14 12 19 21 14"/>',
  "layout-dashboard": '<rect x="3" y="3" width="8" height="9" rx="1"/><rect x="13" y="3" width="8" height="5" rx="1"/><rect x="13" y="10" width="8" height="11" rx="1"/><rect x="3" y="14" width="8" height="7" rx="1"/>',
  "chart-line": '<polyline points="3 17 9 11 13 15 21 6"/><polyline points="15 6 21 6 21 12"/>',
  image: '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="9" r="1.5"/><path d="M21 15l-5-5-9 9"/>',
  "circle-help": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.9.4-1.5 1-1.5 2.2"/><line x1="12" y1="17" x2="12" y2="17.01"/>',
  calculator: '<rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="11" x2="8" y2="11.01"/><line x1="12" y1="11" x2="12" y2="11.01"/><line x1="16" y1="11" x2="16" y2="11.01"/><line x1="8" y1="15" x2="8" y2="15.01"/><line x1="12" y1="15" x2="12" y2="15.01"/><line x1="16" y1="15" x2="16" y2="18"/><line x1="8" y1="18" x2="8" y2="18.01"/><line x1="12" y1="18" x2="12" y2="18.01"/>',
  trophy: '<path d="M8 21h8"/><path d="M12 17v4"/><path d="M7 4h10v5a5 5 0 0 1-10 0V4Z"/><path d="M17 5h2a2 2 0 0 1 0 4h-2"/><path d="M7 5H5a2 2 0 0 0 0 4h2"/>',
};

function icon(name, { size = 16, className = "" } = {}) {
  const body = ICON_PATHS[name] || "";
  return `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${className}" aria-hidden="true">${body}</svg>`;
}

// The mycat brand mark: a single stethoscope tube bent into a cat's head, the
// earpieces landing on the ear tips and the chestpiece hanging below. Matches
// the "00 — Logo" board in the MCAT mockups. The head always fills white; the
// outline, ears and stethoscope are currentColor so they follow the text
// colour; the eyes, mouth and whiskers use --mark-face (the text colour too,
// except in dark mode, where they switch to dark ink so they show on the
// white face). The nose stays a fixed pink. Whiskers and mouth are dropped
// below ~20px where they'd blur.
function mycatMark(size = 26) {
  const face = 'style="stroke:var(--mark-face, currentColor)"';
  const detail = size >= 20
    ? `<path d="M32 37.8 L32 39.1 M32 39.1 C30.9 41.3 28.6 41.1 27.8 39.4 M32 39.1 C33.1 41.3 35.4 41.1 36.2 39.4" stroke="currentColor" ${face} stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M21.5 34.6 L15.8 33.2 M21.5 37.4 L16.2 39.2 M42.5 34.6 L48.2 33.2 M42.5 37.4 L47.8 39.2" stroke="currentColor" ${face} stroke-width="2" stroke-linecap="round"/>`
    : "";
  return `<svg viewBox="0 0 64 64" width="${size}" height="${size}" fill="none" style="flex:none" aria-hidden="true"><path d="M13 10 C15.5 15.2 20 18.6 25.5 20.2 C29.4 18 34.6 18 38.5 20.2 C44 18.6 48.5 15.2 51 10 C54 17.5 54.2 28 51.5 35.2 C49 44 41 48.6 32 48.6 C23 48.6 15 44 12.5 35.2 C9.8 28 10 17.5 13 10 Z" fill="#ffffff" stroke="currentColor" stroke-width="4.5" stroke-linejoin="round" stroke-linecap="round"/><circle cx="13" cy="9" r="4.5" fill="currentColor"/><circle cx="51" cy="9" r="4.5" fill="currentColor"/><path d="M32 48.5 C32 54 36 56.5 40 57" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"/><circle cx="46.5" cy="57" r="5.5" stroke="currentColor" stroke-width="4.5"/><circle cx="24.5" cy="30.5" r="2.8" fill="currentColor" style="fill:var(--mark-face, currentColor)"/><circle cx="39.5" cy="30.5" r="2.8" fill="currentColor" style="fill:var(--mark-face, currentColor)"/><ellipse cx="32" cy="35.6" rx="2.7" ry="2.2" fill="#f0879e"/>${detail}</svg>`;
}
