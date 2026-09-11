// Exports missed questions as a file Anki can import (File > Import on
// desktop). It's Anki's tab-separated text format with #header lines, so the
// importer picks the note type, deck, HTML mode and tag column on its own.
// One Basic note per question: the front has the passage (if any), figure,
// question and choices; the back has the answer and explanation.
const AnkiExport = (function () {
  const LETTERS = ["A", "B", "C", "D"];
  const HEADER = [
    "#separator:tab",
    "#html:true",
    "#notetype:Basic",
    "#deck:MyCat::Missed questions",
    "#tags column:3",
  ].join("\n") + "\n";

  // Missed = the most recent answer was wrong (practice or full exam), or
  // the flashcard was last graded "Again". Getting it right later drops it.
  function missedQuestions() {
    const s = Store.load();
    const latest = {};
    s.answerLog.forEach((a) => { latest[a.qid] = a.correct; });
    const ids = new Set(Object.keys(latest).filter((id) => latest[id] === false));
    Object.entries(s.cards).forEach(([id, c]) => { if (c.lastCorrect === false) ids.add(id); });
    return [...ids].map((id) => Data.allQuestions[id]).filter(Boolean);
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  }
  const text = (s) => esc(s).replace(/\r?\n/g, "<br>");
  const tag = (s) => String(s || "").replace(/[^A-Za-z0-9]+/g, "_").replace(/^_|_$/g, "");

  // Anki reads quoted fields, which lets the SVG figures keep their quotes;
  // tabs and stray newlines would otherwise split the row.
  const field = (html) => `"${html.replace(/[\t\r\n]+/g, " ").replace(/"/g, '""')}"`;

  function row(q) {
    const front =
      (q.passage ? `<div style="text-align:left;font-size:.85em;margin-bottom:1em">${text(q.passage)}</div>` : "") +
      (q.figure || "") +
      `<div style="text-align:left"><b>${text(q.question)}</b></div>` +
      `<ol type="A" style="text-align:left">${q.options.map((o) => `<li>${text(o)}</li>`).join("")}</ol>`;
    const back =
      `<div style="text-align:left"><b>Answer: ${LETTERS[q.correct]}.</b> ${text(q.options[q.correct])}` +
      `<br><br>${text(q.explanation)}` +
      `<br><br><small>${esc(q.section || "")}${q.topic ? " · " + esc(q.topic) : ""}</small></div>`;
    const tags = ["mycat", "missed", tag(q.section), tag(q.topic)].filter(Boolean).join(" ");
    return [field(front), field(back), tags].join("\t");
  }

  // Builds the file and hands it to the browser as a download. Returns how
  // many questions went into it (0 means nothing was downloaded).
  function download() {
    const qs = missedQuestions();
    if (!qs.length) return 0;
    const blob = new Blob([HEADER + qs.map(row).join("\n") + "\n"], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `mycat-missed-${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    // iOS shows a save sheet first, so don't pull the file out from under it.
    setTimeout(() => URL.revokeObjectURL(url), 60000);
    return qs.length;
  }

  // Shared button markup + wiring for the pages that offer the export.
  function buttonHTML(count) {
    return `<button type="button" class="btn btn-secondary" data-anki-export>${icon("download", { size: 15 })}Export ${count} missed to Anki</button>`;
  }
  function bind(scope) {
    (scope || document).querySelectorAll("[data-anki-export]").forEach((btn) => {
      btn.addEventListener("click", () => download());
    });
  }

  return { missedQuestions, download, buttonHTML, bind };
})();
