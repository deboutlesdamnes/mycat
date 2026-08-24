// Pure functions computing dashboard/exam/schedule stats from real state
// (Store.load() + Data). Nothing here is hardcoded sample data — every
// number is derived from the user's own answer history, or is explicitly
// an "estimate"/"approximate" heuristic clearly labeled as such in the UI.
const Stats = (function () {
  const DAY_MS = 24 * 60 * 60 * 1000;

  function dayKey(ts) { return new Date(ts).toISOString().slice(0, 10); }

  function bySection(answerLog) {
    const out = {};
    answerLog.forEach((a) => {
      if (!a.section) return;
      out[a.section] = out[a.section] || { correct: 0, total: 0 };
      out[a.section].total += 1;
      if (a.correct) out[a.section].correct += 1;
    });
    return out;
  }

  function byTopic(answerLog) {
    const out = {};
    answerLog.forEach((a) => {
      if (!a.topic) return;
      out[a.topic] = out[a.topic] || { correct: 0, total: 0, section: a.section };
      out[a.topic].total += 1;
      if (a.correct) out[a.topic].correct += 1;
    });
    return out;
  }

  function accuracy(bucket) {
    if (!bucket || !bucket.total) return null;
    return bucket.correct / bucket.total;
  }

  function weakestTopics(answerLog, n = 5, minAttempts = 3) {
    const topics = byTopic(answerLog);
    return Object.entries(topics)
      .filter(([, b]) => b.total >= minAttempts)
      .map(([topic, b]) => ({ topic, section: b.section, total: b.total, accuracy: accuracy(b) }))
      .sort((a, b) => a.accuracy - b.accuracy)
      .slice(0, n);
  }

  // AAMC-style per-section scale is roughly 118-132; map accuracy linearly
  // onto that range. This is a rough estimate, always labeled as such in UI.
  function estimateSectionScore(acc) {
    if (acc == null) return null;
    return Math.round(Math.max(118, Math.min(132, 118 + acc * 14)));
  }

  function estimateComposite(answerLog, sections) {
    const totalAnswered = answerLog.length;
    if (totalAnswered < 5) return null;
    const secAcc = bySection(answerLog);
    let sum = 0;
    sections.forEach((s) => {
      const acc = accuracy(secAcc[s]);
      sum += acc == null ? 125 : estimateSectionScore(acc);
    });
    return sum;
  }

  // Rough public percentile bands for the 472-528 composite scale, linearly
  // interpolated between anchors. Approximate — labeled as such wherever shown.
  const PCTL_ANCHORS = [
    [472, 1], [480, 5], [486, 10], [490, 16], [494, 24], [498, 33], [500, 40],
    [502, 46], [504, 53], [506, 60], [508, 66], [510, 72], [512, 78], [514, 83],
    [516, 87], [518, 91], [520, 94], [522, 96], [524, 98], [526, 99], [528, 100],
  ];
  function approxPercentile(score) {
    if (score == null) return null;
    const s = Math.max(472, Math.min(528, score));
    for (let i = 1; i < PCTL_ANCHORS.length; i++) {
      const [x0, y0] = PCTL_ANCHORS[i - 1];
      const [x1, y1] = PCTL_ANCHORS[i];
      if (s <= x1) return Math.round(y0 + (y1 - y0) * (s - x0) / (x1 - x0));
    }
    return 100;
  }

  function streak(activityLog) {
    const today = new Date();
    const hasToday = (activityLog[dayKey(today.getTime())] || 0) > 0;
    let cursor = new Date(today);
    if (!hasToday) {
      cursor.setDate(cursor.getDate() - 1);
      if ((activityLog[dayKey(cursor.getTime())] || 0) <= 0) return 0;
    }
    let n = 0;
    while ((activityLog[dayKey(cursor.getTime())] || 0) > 0) {
      n += 1;
      cursor.setDate(cursor.getDate() - 1);
    }
    return n;
  }

  function weeklyMinutes(activityLog) {
    const labels = ["S", "M", "T", "W", "T", "F", "S"];
    const out = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      out.push({ label: labels[d.getDay()], minutes: Math.round(activityLog[dayKey(d.getTime())] || 0), isToday: i === 0 });
    }
    return out;
  }

  function scoreDeltaOverDays(answerLog, sections, days) {
    const now = Date.now();
    const recent = estimateComposite(answerLog, sections);
    const past = estimateComposite(answerLog.filter((a) => a.date <= now - days * DAY_MS), sections);
    if (recent == null || past == null) return null;
    return recent - past;
  }

  // ---------------- adaptive queue ----------------
  function dueCards(store) {
    const s = store;
    const now = Date.now();
    return Object.entries(s.cards)
      .filter(([, c]) => c.due && c.due <= now)
      .map(([qid, c]) => ({ qid, ...c }))
      .sort((a, b) => a.due - b.due);
  }

  function adaptiveQueue(store, data) {
    const items = [];
    const due = dueCards(store);
    if (due.length) {
      items.push({
        key: "due", tag: "Due", tagClass: "tag2-accent",
        title: "Review due cards", subtitle: `${due.length} card${due.length === 1 ? "" : "s"} · spaced repetition`,
        href: "practice.html?mode=due",
      });
    }

    const weak = weakestTopics(store.answerLog, 1);
    if (weak.length) {
      const w = weak[0];
      items.push({
        key: "weak", tag: "Priority", tagClass: "tag2-accent",
        title: `Weak-area drill · ${w.topic}`,
        subtitle: `${Math.round(w.accuracy * 100)}% accuracy so far`,
        href: `practice.html?mode=topic&topic=${encodeURIComponent(w.topic)}`,
      });
    }

    const carsSection = "Critical Analysis and Reasoning Skills";
    const hasCars = data.allDecks.some((d) => d.questions.some((q) => q.section === carsSection));
    const today = dayKey(Date.now());
    const answeredCarsToday = store.answerLog.some((a) => a.section === carsSection && dayKey(a.date) === today);
    if (hasCars && !answeredCarsToday) {
      items.push({
        key: "cars", tag: "Daily", tagClass: "tag2-neutral",
        title: "CARS passage set", subtitle: "Keep your daily CARS reps going",
        href: `practice.html?mode=section&section=${encodeURIComponent(carsSection)}`,
      });
    }

    if (store.flagged.length) {
      items.push({
        key: "flagged", tag: "Flagged", tagClass: "tag2-neutral",
        title: `Review ${store.flagged.length} flagged question${store.flagged.length === 1 ? "" : "s"}`,
        subtitle: "Questions you marked for a second look",
        href: "practice.html?mode=flagged",
      });
    }

    if (!items.length) {
      items.push({
        key: "new", tag: "New", tagClass: "tag2-neutral",
        title: "Start practicing", subtitle: "No review due yet — begin a new set",
        href: "practice.html",
      });
    }
    return items.slice(0, 5);
  }

  // ---------------- schedule generator ----------------
  function generateSchedule(profile, data, testAttempts) {
    if (!profile.testDate) return null;
    const start = new Date();
    start.setHours(0, 0, 0, 0);
    const end = new Date(profile.testDate);
    if (isNaN(end.getTime()) || end <= start) return null;

    const maxDays = 12 * 7;
    const totalDays = Math.min(maxDays, Math.round((end - start) / DAY_MS));
    const weeklyHours = profile.weeklyHours || 15;
    const sessionsPerWeek = Math.max(2, Math.min(7, Math.round(weeklyHours / 1.5)));

    const rotation = [
      { type: "practice", label: "QBank · practice set" },
      { type: "review", label: "Content review" },
      { type: "cars", label: "CARS · 3 passages" },
      { type: "practice", label: "Weak-area drill" },
      { type: "review", label: "Flagged question review" },
    ];

    const sittingsDone = testAttempts.filter((a) => a.kind === "sitting").length;
    const weeksTotal = Math.max(1, Math.round(totalDays / 7));
    const examsToSchedule = Math.max(0, Math.min(6, Math.floor(weeksTotal / 2)) - sittingsDone);

    const days = {};
    let rot = 0;
    for (let i = 0; i < totalDays; i++) {
      const d = new Date(start);
      d.setDate(d.getDate() + i);
      const dow = d.getDay(); // 0=Sun
      const key = dayKey(d.getTime());
      const isRestDay = dow === 0;
      if (isRestDay) {
        days[key] = [{ type: "rest", label: "Rest day" }];
        continue;
      }
      const weekIndex = Math.floor(i / 7);
      const sessionSlotsThisWeek = sessionsPerWeek;
      const dayOfWeekIndex = dow; // 1..6 mon..sat
      if (dayOfWeekIndex > sessionSlotsThisWeek) continue; // no task scheduled, quiet day
      const task = rotation[rot % rotation.length];
      rot += 1;
      days[key] = [task];
    }

    // Space full-length sittings roughly every 2 weeks, on Saturdays.
    let examsPlaced = 0;
    for (let w = 1; w <= weeksTotal && examsPlaced < examsToSchedule; w += 2) {
      const satOffset = (w - 1) * 7 + (6 - start.getDay() + 7) % 7;
      if (satOffset >= totalDays) break;
      const d = new Date(start);
      d.setDate(d.getDate() + satOffset);
      const key = dayKey(d.getTime());
      days[key] = [{ type: "exam", label: "Full-length exam day" }];
      examsPlaced += 1;
    }

    return { generatedAt: Date.now(), testDate: profile.testDate, weeklyHours, days };
  }

  return {
    bySection, byTopic, accuracy, weakestTopics,
    estimateSectionScore, estimateComposite, approxPercentile,
    streak, weeklyMinutes, scoreDeltaOverDays,
    dueCards, adaptiveQueue, generateSchedule, dayKey,
  };
})();
