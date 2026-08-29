// Accounts + cross-device progress sync.
//
// Two modes:
//   • "supabase" — when supabase-config.js has a URL + anon key, uses Supabase
//     Auth + the `profiles` table for real accounts and cross-device sync.
//   • "local"    — fallback when Supabase isn't configured. Accounts live in
//     this browser's localStorage (email + salted SHA-256-hashed password via
//     Web Crypto); progress is isolated per account. No backend required.
//
// Sync model (supabase mode): localStorage stays the single source of truth
// the rest of the app reads/writes synchronously. On sign-in we pull the
// remote copy, MERGE it with local (mergeStates never drops card progress),
// write the merged result back, and thereafter push a debounced copy whenever
// Store.save() reports a local change. Local mode does no remote I/O.
const Auth = (function () {
  const cfg = window.SUPABASE_CONFIG || {};
  const supabaseReady = typeof window.supabase !== "undefined" && !!window.supabase.createClient;
  const supabaseConfigured = supabaseReady && !!cfg.url && !!cfg.anonKey;
  const mode = supabaseConfigured ? "supabase" : "local";

  const LOCAL_KEY = "mycat_local_auth_v1";
  const GUEST_KEY = "mycat_state_v2";

  let client = null;
  let currentUser = null;      // Supabase user object OR local account object
  let recoveryMode = false;
  let applyingRemote = false;   // guard: don't echo a remote-driven save back out
  let syncInFlight = null;      // collapse concurrent syncNow() calls
  let pushTimer = null;
  const listeners = new Set();

  if (mode === "supabase") {
    client = window.supabase.createClient(cfg.url, cfg.anonKey, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
    });
  }

  function notify() {
    listeners.forEach((fn) => { try { fn(currentUser); } catch (e) { /* listener errors are its own problem */ } });
  }

  // ---- local account store ----
  function localLoad() {
    try {
      return JSON.parse(localStorage.getItem(LOCAL_KEY)) || { accounts: [], session: null };
    } catch (e) {
      return { accounts: [], session: null };
    }
  }
  function localSave(a) {
    try { localStorage.setItem(LOCAL_KEY, JSON.stringify(a)); } catch (e) { /* ignore */ }
  }

  async function hashPassword(password, salt) {
    if (!(window.crypto && window.crypto.subtle)) {
      throw new Error("Secure password hashing isn't available here. Open the site over HTTPS or http://localhost.");
    }
    const data = new TextEncoder().encode(salt + ":" + password);
    const buf = await crypto.subtle.digest("SHA-256", data);
    return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join("");
  }
  function newSalt() {
    const arr = new Uint8Array(16);
    crypto.getRandomValues(arr);
    return Array.from(arr).map((b) => b.toString(16).padStart(2, "0")).join("");
  }
  function migrateGuestTo(uid) {
    try {
      const guest = localStorage.getItem(GUEST_KEY);
      const target = GUEST_KEY + "_" + uid;
      if (guest && !localStorage.getItem(target)) localStorage.setItem(target, guest);
    } catch (e) { /* ignore */ }
  }

  // ---- session sniff (synchronous, for optimistic nav rendering) ----
  function hasStoredSession() {
    if (mode === "local") return !!localLoad().session;
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        if (k && k.startsWith("sb-") && k.endsWith("-auth-token")) {
          const v = localStorage.getItem(k);
          if (v && v.length > 20) return true;
        }
      }
    } catch (e) { /* private mode */ }
    return false;
  }

  // ---- state merge: order-independent enough, never loses card progress ----
  function emptyState() {
    return {
      cards: {}, saved: [], flagged: [], profile: {}, answerLog: [],
      testAttempts: [], activityLog: {}, schedule: null, lastAnswerAt: 0, updatedAt: 0,
    };
  }

  function mergeStates(a, b) {
    a = a || emptyState();
    b = b || emptyState();
    const out = emptyState();

    // cards: keep the more-studied copy (tiebreak: further-out due date)
    const ids = new Set([...Object.keys(a.cards || {}), ...Object.keys(b.cards || {})]);
    ids.forEach((id) => {
      const ca = (a.cards || {})[id];
      const cb = (b.cards || {})[id];
      if (!ca) { out.cards[id] = cb; return; }
      if (!cb) { out.cards[id] = ca; return; }
      const sa = ca.seen || 0, sb = cb.seen || 0;
      out.cards[id] = sa === sb ? ((ca.due || 0) >= (cb.due || 0) ? ca : cb) : (sa > sb ? ca : cb);
    });

    out.saved = Array.from(new Set([...(a.saved || []), ...(b.saved || [])]));
    out.flagged = Array.from(new Set([...(a.flagged || []), ...(b.flagged || [])]));

    const seenLog = new Set();
    out.answerLog = [...(a.answerLog || []), ...(b.answerLog || [])]
      .filter((e) => { const k = e.qid + "|" + e.date; if (seenLog.has(k)) return false; seenLog.add(k); return true; })
      .sort((x, y) => x.date - y.date)
      .slice(-5000);

    const seenAtt = new Set();
    out.testAttempts = [...(a.testAttempts || []), ...(b.testAttempts || [])]
      .filter((t) => { if (seenAtt.has(t.date)) return false; seenAtt.add(t.date); return true; })
      .sort((x, y) => x.date - y.date)
      .slice(-200);

    out.activityLog = { ...(a.activityLog || {}) };
    Object.entries(b.activityLog || {}).forEach(([day, min]) => {
      out.activityLog[day] = Math.max(out.activityLog[day] || 0, min);
    });

    // profile: prefer the "more onboarded" snapshot, tiebreak by recency
    const pa = a.profile || {}, pb = b.profile || {};
    if (pa.onboarded && !pb.onboarded) out.profile = { ...pb, ...pa };
    else if (pb.onboarded && !pa.onboarded) out.profile = { ...pa, ...pb };
    else out.profile = (b.updatedAt || 0) > (a.updatedAt || 0) ? { ...pa, ...pb } : { ...pb, ...pa };

    const sa = a.schedule, sb = b.schedule;
    out.schedule = (sb && (!sa || (sb.generatedAt || 0) >= (sa.generatedAt || 0))) ? sb : sa;
    out.lastAnswerAt = Math.max(a.lastAnswerAt || 0, b.lastAnswerAt || 0);
    out.updatedAt = Date.now();
    return out;
  }

  function materiallyChanged(before, after) {
    const b = before.profile || {}, a = after.profile || {};
    if (!!b.onboarded !== !!a.onboarded) return true;
    if (Object.keys(before.cards || {}).length !== Object.keys(after.cards || {}).length) return true;
    if ((before.answerLog || []).length !== (after.answerLog || []).length) return true;
    if ((before.testAttempts || []).length !== (after.testAttempts || []).length) return true;
    if ((before.saved || []).length !== (after.saved || []).length) return true;
    return false;
  }

  // ---- remote I/O (supabase only) ----
  async function pullRemote() {
    const { data, error } = await client
      .from("profiles").select("state").eq("user_id", currentUser.id).maybeSingle();
    if (error) { console.warn("[MyCat sync] pull failed:", error.message); throw error; }
    return data ? data.state : undefined;
  }

  async function pushRemote(state) {
    const { error } = await client.from("profiles").upsert(
      { user_id: currentUser.id, state, updated_at: new Date().toISOString() },
      { onConflict: "user_id" },
    );
    if (error) console.warn("[MyCat sync] push failed:", error.message);
    return !error;
  }

  async function runSync() {
    const local = Store.load();
    let remote;
    try { remote = await pullRemote(); } catch (e) { return false; }
    const merged = mergeStates(local, remote);
    applyingRemote = true;
    try { Store.save(merged); } finally { applyingRemote = false; }
    await pushRemote(merged);
    notify();
    return materiallyChanged(local, merged);
  }

  function syncNow() {
    if (mode !== "supabase" || !currentUser) return Promise.resolve(false);
    if (syncInFlight) return syncInFlight;
    syncInFlight = runSync().finally(() => { syncInFlight = null; });
    return syncInFlight;
  }

  // ---- debounced push on local change (called from Store.save) ----
  function notifyLocalChange() {
    if (mode !== "supabase" || !currentUser || applyingRemote) return;
    clearTimeout(pushTimer);
    pushTimer = setTimeout(() => { pushRemote(Store.load()); }, 1500);
  }

  function flushPush() {
    if (mode !== "supabase" || !currentUser) return;
    clearTimeout(pushTimer);
    pushRemote(Store.load());
  }

  // ---- auth actions ----
  async function signUp(email, password) {
    if (mode === "supabase") {
      const { data, error } = await client.auth.signUp({ email, password });
      if (error) throw error;
      currentUser = data.session ? data.user : null;
      if (currentUser) await syncNow();
      return data; // { user, session } — session is null when email confirmation is required
    }

    email = (email || "").trim().toLowerCase();
    if (!email || !password) throw new Error("Email and password are required.");
    if (password.length < 8) throw new Error("Password must be at least 8 characters.");
    const a = localLoad();
    if (a.accounts.some((u) => u.email === email)) {
      throw new Error("An account with this email already exists. Log in instead.");
    }
    const salt = newSalt();
    const hash = await hashPassword(password, salt);
    const user = {
      id: "u_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8),
      email, salt, hash, createdAt: Date.now(),
    };
    a.accounts.push(user);
    a.session = user.id;
    localSave(a);
    migrateGuestTo(user.id);
    currentUser = user;
    notify();
    return { user, session: { user } }; // session is truthy → account.js redirects
  }

  async function signIn(email, password) {
    if (mode === "supabase") {
      const { data, error } = await client.auth.signInWithPassword({ email, password });
      if (error) throw error;
      currentUser = data.user;
      await syncNow();
      return data.user;
    }

    email = (email || "").trim().toLowerCase();
    const a = localLoad();
    const user = a.accounts.find((u) => u.email === email);
    if (!user) throw new Error("No account found with that email.");
    const hash = await hashPassword(password, user.salt);
    if (hash !== user.hash) throw new Error("Incorrect password.");
    a.session = user.id;
    localSave(a);
    currentUser = user;
    notify();
    return user;
  }

  async function signOut() {
    if (mode === "supabase") {
      flushPush();
      if (client) { try { await client.auth.signOut(); } catch (e) { /* already gone */ } }
    } else {
      const a = localLoad();
      a.session = null;
      localSave(a);
    }
    currentUser = null;
    recoveryMode = false;
    notify();
  }

  function resetPassword(email) {
    if (mode === "supabase") {
      return client.auth.resetPasswordForEmail(email, { redirectTo: location.origin + "/account.html" });
    }
    return Promise.reject(new Error(
      "Password reset isn't available for local accounts. Log in with your password, or create a new account."
    ));
  }

  async function updatePassword(password) {
    if (mode === "supabase") {
      const { error } = await client.auth.updateUser({ password });
      if (error) throw error;
      recoveryMode = false;
      return;
    }

    if (!password || password.length < 8) throw new Error("Password must be at least 8 characters.");
    const a = localLoad();
    const user = a.accounts.find((u) => u.id === a.session);
    if (!user) throw new Error("Not signed in.");
    user.salt = newSalt();
    user.hash = await hashPassword(password, user.salt);
    localSave(a);
    recoveryMode = false;
  }

  // ---- init ----
  async function initSupabase() {
    const { data } = await client.auth.getSession();
    currentUser = data && data.session ? data.session.user : null;

    client.auth.onAuthStateChange((event, session) => {
      currentUser = session ? session.user : null;
      if (event === "PASSWORD_RECOVERY") recoveryMode = true;
      if (event === "SIGNED_IN") syncNow();
      notify();
    });

    if (currentUser) {
      const changed = await syncNow();
      // Fresh device / cleared progress: local state just gained the account's
      // history. Reload once so pages that already rendered pick it up.
      if (changed && !sessionStorage.getItem("mycat_sync_reloaded")) {
        try { sessionStorage.setItem("mycat_sync_reloaded", "1"); } catch (e) {}
        location.reload();
        return;
      }
    }
    notify();

    window.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") flushPush();
    });
    window.addEventListener("pagehide", flushPush);
  }

  function initLocal() {
    const a = localLoad();
    currentUser = a.accounts.find((u) => u.id === a.session) || null;
    notify();
  }

  const api = {
    get mode() { return mode; },
    get enabled() { return true; },   // accounts are always available (local fallback)
    get recoveryMode() { return recoveryMode; },
    libLoaded: true,                  // no external dependency in local mode
    user() { return currentUser; },
    localUser() { return mode === "local" ? currentUser : null; },
    email() { return currentUser ? currentUser.email : null; },
    hasStoredSession,
    onChange(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    signUp, signIn, signOut, resetPassword, updatePassword,
    syncNow, notifyLocalChange, mergeStates,
    ready: Promise.resolve(),
  };

  if (mode === "supabase") {
    api.ready = initSupabase().catch((e) => { console.warn("[MyCat auth] init failed:", e); });
  } else {
    initLocal();
  }

  return api;
})();
