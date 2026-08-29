(function () {
  renderNav("account");
  const root = document.getElementById("page-root");

  let tab = "login"; // "login" | "signup"

  function esc(s) {
    return String(s).replace(/[&<>"']/g, (c) => (
      { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
    ));
  }

  function shell(inner) {
    return `<div class="panel panel-pad" style="max-width:460px;margin:0 auto;width:100%">${inner}</div>`;
  }

  function notConfigured(body) {
    return shell(`
      <div class="k" style="margin-bottom:8px">Account</div>
      <h1 style="font-size:28px;margin-bottom:12px">Sync isn't set up</h1>
      <p class="text-muted">${body}</p>
      <hr class="hr">
      <a class="btn btn-primary" href="index.html">Continue to MyCat</a>
    `);
  }

  function msgRow() {
    return `<div id="acct-msg" class="text-muted" style="font-size:12px;min-height:16px;margin-top:10px"></div>`;
  }

  function setMsg(text, kind) {
    const el = document.getElementById("acct-msg");
    if (!el) return;
    el.textContent = text || "";
    el.style.color = kind === "error" ? "var(--color-wrong)"
      : kind === "ok" ? "var(--color-correct)"
      : "";
  }

  function renderRecovery() {
    root.innerHTML = shell(`
      <div class="k" style="margin-bottom:8px">Account</div>
      <h1 style="font-size:28px;margin-bottom:12px">Choose a new password</h1>
      <form id="recovery-form">
        <div class="field" style="margin-bottom:14px">
          <label>New password</label>
          <input class="input" type="password" id="rp-pass" autocomplete="new-password" minlength="8" required>
        </div>
        <button type="submit" class="btn btn-primary btn-block" style="justify-content:center">Update password</button>
        ${msgRow()}
      </form>
    `);
    document.getElementById("recovery-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      setMsg("Updating…");
      try {
        await Auth.updatePassword(document.getElementById("rp-pass").value);
        setMsg("Password updated. Redirecting…", "ok");
        setTimeout(() => { location.href = "index.html"; }, 900);
      } catch (err) {
        setMsg(err.message || "Could not update password.", "error");
      }
    });
  }

  function renderSignedIn() {
    const email = Auth.email() || "your account";
    const callout = Auth.mode === "supabase"
      ? `<div class="callout" style="margin-bottom:18px">
          <div class="k">Cross-device sync is on</div>
          <p>Your progress, saved cards, stats and study plan sync automatically to this account whenever they change.</p>
        </div>`
      : `<div class="callout" style="margin-bottom:18px">
          <div class="k">Account active</div>
          <p>Your progress, saved cards, stats and study plan are saved to this account in this browser.</p>
        </div>`;
    root.innerHTML = shell(`
      <div class="k" style="margin-bottom:8px">Account</div>
      <h1 style="font-size:28px;margin-bottom:6px">Signed in</h1>
      <p class="text-muted" style="margin-bottom:16px">${esc(email)}</p>
      ${callout}
      <div style="display:flex;gap:10px;flex-wrap:wrap">
        <button class="btn btn-secondary" id="btn-sync">Sync now</button>
        <button class="btn btn-secondary" id="btn-signout">Log out</button>
        <a class="btn btn-primary" href="index.html">Go to dashboard</a>
      </div>
      ${msgRow()}
    `);

    document.getElementById("btn-sync").addEventListener("click", async () => {
      setMsg("Syncing…");
      await Auth.syncNow();
      setMsg("Synced.", "ok");
    });
    document.getElementById("btn-signout").addEventListener("click", async () => {
      setMsg("Logging out…");
      await Auth.signOut();
      render();
    });
  }

  function renderSignedOut() {
    const isSignup = tab === "signup";
    root.innerHTML = shell(`
      <div class="k" style="margin-bottom:8px">Account</div>
      <h1 style="font-size:28px;margin-bottom:6px">${isSignup ? "Create your account" : "Log in"}</h1>
      <p class="text-muted" style="margin-bottom:16px">
        ${Auth.mode === "supabase"
          ? (isSignup
              ? "An account keeps your progress synced across every device you study on."
              : "Welcome back — pick up where you left off on any device.")
          : (isSignup
              ? "Create a local account to keep your progress separate and saved in this browser."
              : "Welcome back — log in to your local account.")}
      </p>

      <div class="seg" style="width:100%;margin-bottom:18px">
        <label class="seg-opt" style="flex:1;justify-content:center">
          <input type="radio" name="acct-tab" value="login" ${isSignup ? "" : "checked"}>Log in
        </label>
        <label class="seg-opt" style="flex:1;justify-content:center">
          <input type="radio" name="acct-tab" value="signup" ${isSignup ? "checked" : ""}>Sign up
        </label>
      </div>

      <form id="acct-form">
        <div class="field" style="margin-bottom:14px">
          <label>Email</label>
          <input class="input" type="email" id="acct-email" autocomplete="email" required>
        </div>
        <div class="field" style="margin-bottom:6px">
          <label>Password</label>
          <input class="input" type="password" id="acct-pass"
                 autocomplete="${isSignup ? "new-password" : "current-password"}"
                 minlength="${isSignup ? 8 : 1}" required>
        </div>
        ${isSignup
          ? '<div class="text-muted" style="font-size:11px;margin-bottom:12px">At least 8 characters.</div>'
          : (Auth.mode === "supabase"
              ? '<button type="button" class="text-link" id="acct-forgot" style="margin-bottom:12px">Forgot password?</button>'
              : '')}
        <button type="submit" class="btn btn-primary btn-block" style="justify-content:center;margin-top:6px">
          ${isSignup ? "Create account" : "Log in"}
        </button>
        ${msgRow()}
      </form>

      <hr class="hr">
      <a class="text-link" href="index.html">Continue without an account →</a>
      <p class="text-muted" style="font-size:11px;margin-top:10px">
        Progress made without an account stays in this browser and is merged in when you first log in.
      </p>
    `);

    root.querySelectorAll('input[name="acct-tab"]').forEach((r) => {
      r.addEventListener("change", (e) => { tab = e.target.value; renderSignedOut(); });
    });

    const forgot = document.getElementById("acct-forgot");
    if (forgot) {
      forgot.addEventListener("click", async () => {
        const email = document.getElementById("acct-email").value.trim();
        if (!email) { setMsg("Enter your email above first.", "error"); return; }
        setMsg("Sending reset link…");
        try {
          await Auth.resetPassword(email);
          setMsg("Check your email for a password reset link.", "ok");
        } catch (err) {
          setMsg(err.message || "Could not send reset email.", "error");
        }
      });
    }

    document.getElementById("acct-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("acct-email").value.trim();
      const pass = document.getElementById("acct-pass").value;
      const btn = e.target.querySelector('button[type="submit"]');
      btn.disabled = true;
      setMsg(isSignup ? "Creating account…" : "Logging in…");
      try {
        if (isSignup) {
          const res = await Auth.signUp(email, pass);
          if (res.session) {
            location.href = "index.html";
          } else {
            setMsg("Account created. Check your email to confirm, then log in.", "ok");
            tab = "login";
            renderSignedOut();
          }
        } else {
          await Auth.signIn(email, pass);
          location.href = "index.html";
        }
      } catch (err) {
        btn.disabled = false;
        setMsg(err.message || "Something went wrong. Try again.", "error");
      }
    });
  }

  function render() {
    if (typeof Auth === "undefined" || !Auth.libLoaded) {
      root.innerHTML = notConfigured(
        "The account library didn't load — you may be offline or it may be blocked. " +
        "Your progress is still saved in this browser.");
      return;
    }
    if (!Auth.enabled) {
      root.innerHTML = notConfigured(
        "Accounts aren't configured for this site yet. Add your Supabase URL and anon key " +
        "to <code>supabase-config.js</code> to turn on sign-in and cross-device sync. " +
        "Until then, progress is saved in this browser only.");
      return;
    }
    if (Auth.recoveryMode) { renderRecovery(); return; }
    if (Auth.user()) { renderSignedIn(); return; }
    renderSignedOut();
  }

  render();
  if (typeof Auth !== "undefined") {
    if (Auth.onChange) Auth.onChange(render);
    if (Auth.ready && Auth.ready.then) Auth.ready.then(render);
  }
})();
