// Shared state layer for the new multi-page site. Reads and writes the SAME
// localStorage key ("mycat_state_v2") that the classic quiz.html/app.js pair
// already uses, so SRS progress stays one shared source of truth across old
// and new pages. app.js only ever reads/writes `cards` and `saved` and does
// a read-modify-write of the whole object, so extra top-level keys added
// here round-trip through it safely without any migration needed.
//
// When a local account is signed in (auth.js "local" mode), progress is
// stored under a per-account key ("mycat_state_v2_<id>") instead, so each
// account gets its own isolated progress in this browser.
const GUEST_KEY = "mycat_state_v2";

function storeKey() {
  try {
    const u = (typeof Auth !== "undefined" && Auth.localUser) ? Auth.localUser() : null;
    return u ? GUEST_KEY + "_" + u.id : GUEST_KEY;
  } catch (e) {
    return GUEST_KEY;
  }
}
const DAY_MS = 24 * 60 * 60 * 1000;
const MIN_EASE = 1.3;
const IDLE_CAP_MS = 5 * 60 * 1000; // don't count gaps longer than this as study time

function defaultState() {
  return {
    cards: {},
    saved: [],
    flagged: [],
    profile: { onboarded: false, baselineScore: null, targetScore: null, testDate: null, weeklyHours: null },
    answerLog: [],
    testAttempts: [],
    activityLog: {},
    schedule: null,
    lastAnswerAt: 0,
    updatedAt: 0,
  };
}

const Store = {
  load() {
    let s;
    try {
      s = JSON.parse(localStorage.getItem(storeKey()));
    } catch {
      s = null;
    }
    const d = defaultState();
    if (!s || typeof s !== "object") return d;
    return {
      cards: s.cards || d.cards,
      saved: s.saved || d.saved,
      flagged: s.flagged || d.flagged,
      profile: { ...d.profile, ...(s.profile || {}) },
      answerLog: s.answerLog || d.answerLog,
      testAttempts: s.testAttempts || d.testAttempts,
      activityLog: s.activityLog || d.activityLog,
      schedule: s.schedule || d.schedule,
      lastAnswerAt: s.lastAnswerAt || 0,
      updatedAt: s.updatedAt || 0,
    };
  },

  save(state) {
    try {
      state.updatedAt = Date.now();
      localStorage.setItem(storeKey(), JSON.stringify(state));
    } catch {
      // ignore storage failures (private browsing, quota, etc.)
    }
    // Optional cross-device sync (auth.js). No-op unless signed in.
    if (typeof Auth !== "undefined" && Auth.notifyLocalChange) Auth.notifyLocalChange();
  },

  reset() {
    try { localStorage.removeItem(storeKey()); } catch {}
  },

  // ---------- SRS cards (SM-2), same scheduler as the classic app.js ----------
  getCard(qid) {
    const s = this.load();
    return s.cards[qid] || {
      interval: 0, ease: 2.5, reps: 0, lapses: 0, due: 0,
      lastGrade: null, lastCorrect: null, seen: 0, missed: 0,
    };
  },

  applyGrade(qid, grade) {
    const s = this.load();
    const card = s.cards[qid] || {
      interval: 0, ease: 2.5, reps: 0, lapses: 0, due: 0,
      lastGrade: null, lastCorrect: null, seen: 0, missed: 0,
    };
    card.seen += 1;
    card.lastGrade = grade;

    if (grade === "again") {
      card.lastCorrect = false;
      card.missed += 1;
      card.reps = 0;
      card.lapses += 1;
      card.ease = Math.max(MIN_EASE, card.ease - 0.2);
      card.interval = 10 / (60 * 24);
      card.due = Date.now() + 10 * 60 * 1000;
    } else {
      card.lastCorrect = true;
      if (grade === "hard") {
        card.ease = Math.max(MIN_EASE, card.ease - 0.15);
        card.interval = card.reps === 0 ? 1 : Math.max(card.interval, 0.5) * 1.2;
        card.reps += 1;
      } else if (grade === "good") {
        if (card.reps === 0) card.interval = 1;
        else if (card.reps === 1) card.interval = 6;
        else card.interval = card.interval * card.ease;
        card.reps += 1;
      } else {
        card.ease = Math.min(3.0, card.ease + 0.15);
        card.interval = card.reps === 0 ? 4 : card.interval * card.ease * 1.3;
        card.reps += 1;
      }
      card.due = Date.now() + Math.round(card.interval * DAY_MS);
    }

    s.cards[qid] = card;
    this.save(s);
    return card;
  },

  // ---------- saved / flagged ----------
  isSaved(qid) { return this.load().saved.includes(qid); },
  toggleSaved(qid) {
    const s = this.load();
    const i = s.saved.indexOf(qid);
    if (i >= 0) s.saved.splice(i, 1); else s.saved.push(qid);
    this.save(s);
    return s.saved.includes(qid);
  },
  isFlagged(qid) { return this.load().flagged.includes(qid); },
  toggleFlag(qid) {
    const s = this.load();
    const i = s.flagged.indexOf(qid);
    if (i >= 0) s.flagged.splice(i, 1); else s.flagged.push(qid);
    this.save(s);
    return s.flagged.includes(qid);
  },

  // ---------- profile ----------
  getProfile() { return this.load().profile; },
  setProfile(patch) {
    const s = this.load();
    s.profile = { ...s.profile, ...patch };
    this.save(s);
    return s.profile;
  },

  // ---------- answer log (source of truth for real stats) ----------
  logAnswer({ qid, section, topic, correct, ms }) {
    const s = this.load();
    const now = Date.now();
    s.answerLog.push({ qid, section, topic: topic || null, correct, ms: ms || null, date: now });
    if (s.answerLog.length > 5000) s.answerLog = s.answerLog.slice(-5000);

    // Estimate active study minutes: elapsed time since the previous logged
    // answer, capped so idle gaps (tab left open, came back tomorrow) don't
    // inflate the total.
    const delta = s.lastAnswerAt ? Math.min(now - s.lastAnswerAt, IDLE_CAP_MS) : 60 * 1000;
    const dayKey = new Date(now).toISOString().slice(0, 10);
    s.activityLog[dayKey] = (s.activityLog[dayKey] || 0) + delta / 60000;
    s.lastAnswerAt = now;

    this.save(s);
  },

  // ---------- full-length test attempts ----------
  addTestAttempt(attempt) {
    const s = this.load();
    s.testAttempts.push({ date: Date.now(), ...attempt });
    if (s.testAttempts.length > 200) s.testAttempts = s.testAttempts.slice(-200);
    this.save(s);
  },
  getTestAttempts() { return this.load().testAttempts; },
  tagMissedReason(attemptDate, qid, reason) {
    const s = this.load();
    const a = s.testAttempts.find((t) => t.date === attemptDate);
    if (!a) return;
    a.missedReasons = a.missedReasons || {};
    a.missedReasons[qid] = reason;
    this.save(s);
  },

  // ---------- schedule ----------
  getSchedule() { return this.load().schedule; },
  setSchedule(schedule) {
    const s = this.load();
    s.schedule = schedule;
    this.save(s);
  },
};
