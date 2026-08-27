// Assembles the question bank for the NEW pages (dashboard/practice/etc).
// Mirrors the id scheme app.js uses on quiz.html (`${deck.id}-${i}`) exactly,
// so SRS progress and stats stay consistent whichever page answered a card.
const Data = (function () {
  const decks = typeof DECKS !== "undefined" ? DECKS : [];
  const fullDecks = typeof FULL_DECKS !== "undefined" ? FULL_DECKS : [];
  const hardDecks = typeof HARD_DECKS !== "undefined" ? HARD_DECKS : [];
  const scenarioDecks = typeof SCENARIO_DECKS !== "undefined" ? SCENARIO_DECKS : [];
  const allDecks = decks.concat(fullDecks).concat(hardDecks).concat(scenarioDecks);

  allDecks.forEach((deck) => {
    deck.questions.forEach((q, i) => {
      q.id = `${deck.id}-${i}`;
      q.section = q.section || deck.section;
      q.topic = q.topic || deck.section;
      if (deck.passage) q.passage = q.passage || deck.passage;
    });
  });

  const allQuestions = {};
  allDecks.forEach((d) => d.questions.forEach((q) => { allQuestions[q.id] = q; }));

  const DIFFICULTIES = ["easy", "medium", "hard"];
  function difficultyOf(q) {
    return DIFFICULTIES.includes(q.difficulty) ? q.difficulty : "medium";
  }

  const SECTIONS = [
    "Biological & Biochemical Foundations",
    "Chemical & Physical Foundations",
    "Psychological, Social, & Biological Foundations",
    "Critical Analysis and Reasoning Skills",
  ];

  return { decks, fullDecks, hardDecks, scenarioDecks, allDecks, allQuestions, DIFFICULTIES, difficultyOf, SECTIONS };
})();
