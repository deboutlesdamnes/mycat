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
  plus: '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
  pencil: '<path d="M17 3a2.83 2.83 0 1 1 4 4L7 21l-4 1 1-4Z"/>',
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
