// Optional Supabase-backed accounts + cross-device progress sync.
//
// Entirely opt-in. With no credentials in supabase-config.js, `Auth.enabled`
// is false and the whole app behaves exactly as before — progress lives only
// in this browser's localStorage (see store.js). When configured, signing in
// merges the local progress with whatever is stored for the account and keeps
// the two in sync on every subsequent change.
//
// Sync model: localStorage stays the single source of truth the rest of the
// app reads/writes synchronously. This layer pulls the remote copy on sign-in,
// MERGES it with local (mergeStates never drops card progress), writes the
// merged result back to localStorage, and thereafter pushes a debounced copy
// to Supabase whenever Store.save() reports a local change.
const Auth = (function () {
  const cfg = window.SUPABASE_CONFIG || {};
  const libLoaded = typeof window.supabase !== "undefined" && !!window.supabase.createClient;
  const enabled = libLoaded && !!cfg.url && !!cfg.anonKey;

  let client = null;
  let currentUser = null;
  let recoveryMode = false;
  let applyingRemote = false;   // guard: don't echo a remote-driven save back out
  let syncInFlight = null;      // collapse concurrent syncNow() calls
  let pushTimer = null;
  const listeners = new Set();

  if (enabled) {
    client = window.supabase.createClient(cfg.url, cfg.anonKey, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
    });
  }

  function notify() {
    listeners.forEach((fn) => { try { fn(currentUser); } catch (e) { /* listener errors are its own problem */ } });
  }

  // ---- sync-token sniff (synchronous, for optimistic nav rendering) ----
  function hasStoredSession() {
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

  // ---- remote I/O ----
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
    if (!enabled || !currentUser) return Promise.resolve(false);
    if (syncInFlight) return syncInFlight;
    syncInFlight = runSync().finally(() => { syncInFlight = null; });
    return syncInFlight;
  }

  // ---- debounced push on local change (called from Store.save) ----
  function notifyLocalChange() {
    if (!enabled || !currentUser || applyingRemote) return;
    clearTimeout(pushTimer);
    pushTimer = setTimeout(() => { pushRemote(Store.load()); }, 1500);
  }

  function flushPush() {
    if (!enabled || !currentUser) return;
    clearTimeout(pushTimer);
    pushRemote(Store.load());
  }

  // ---- auth actions ----
  async function signUp(email, password) {
    const { data, error } = await client.auth.signUp({ email, password });
    if (error) throw error;
    currentUser = data.session ? data.user : null;
    if (currentUser) await syncNow();
    return data; // { user, session } — session is null when email confirmation is required
  }

  async function signIn(email, password) {
    const { data, error } = await client.auth.signInWithPassword({ email, password });
    if (error) throw error;
    currentUser = data.user;
    await syncNow();
    return data.user;
  }

  async function signOut() {
    flushPush();
    if (client) { try { await client.auth.signOut(); } catch (e) { /* already gone */ } }
    currentUser = null;
    recoveryMode = false;
    notify();
  }

  function resetPassword(email) {
    return client.auth.resetPasswordForEmail(email, { redirectTo: location.origin + "/account.html" });
  }

  async function updatePassword(password) {
    const { error } = await client.auth.updateUser({ password });
    if (error) throw error;
    recoveryMode = false;
  }

  // ---- init ----
  async function init() {
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

  const api = {
    get enabled() { return enabled; },
    get recoveryMode() { return recoveryMode; },
    libLoaded,
    user() { return currentUser; },
    email() { return currentUser ? currentUser.email : null; },
    hasStoredSession,
    onChange(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    signUp, signIn, signOut, resetPassword, updatePassword,
    syncNow, notifyLocalChange, mergeStates,
    ready: Promise.resolve(),
  };

  if (enabled) api.ready = init().catch((e) => { console.warn("[MyCat auth] init failed:", e); });
  return api;
})();
