// auth.js - Handles both the log-in and the sign-up page.
// Whichever form is on the current page gets wired up; the other is ignored.
//
// Errors are shown right under the field they belong to (in red), so the
// user can see at a glance what to fix. Only problems that aren't about one
// particular field (wrong password, server down...) go in the box at the bottom.

// Already logged in? Skip straight to the dashboard.
if (Session.token()) {
  window.location.replace("/dashboard");
}

const formError = document.getElementById("form-error");

// ---------------------------------------------------------------------------
// Helpers for showing / clearing an error under one field
// ---------------------------------------------------------------------------

function setFieldError(form, name, message) {
  const input = form[name];
  const slot = form.querySelector(`[data-error-for="${name}"]`);
  if (slot) slot.textContent = message || "";
  if (message) {
    input.setAttribute("aria-invalid", "true"); // red outline (see app.css)
  } else {
    input.removeAttribute("aria-invalid");
  }
}

function clearAllErrors(form) {
  form.querySelectorAll("[data-error-for]").forEach((slot) => {
    setFieldError(form, slot.dataset.errorFor, "");
  });
  formError.textContent = "";
}

// Runs every check, shows each error under its own field and returns true
// if everything passed. Also puts the cursor in the first field with a problem.
function showAllErrors(form, checks) {
  let firstBad = null;
  for (const [name, check] of Object.entries(checks)) {
    const message = check(form);
    setFieldError(form, name, message);
    if (message && !firstBad) firstBad = form[name];
  }
  if (firstBad) firstBad.focus();
  return !firstBad;
}

// Check a field as soon as the user leaves it, and clear its error the moment
// they start typing again - so the red text never nags while they're fixing it.
function checkOnBlur(form, checks) {
  for (const [name, check] of Object.entries(checks)) {
    const input = form[name];
    input.addEventListener("blur", () => {
      if (input.value) setFieldError(form, name, check(form));
    });
    input.addEventListener("input", () => setFieldError(form, name, ""));
  }
}

// The server's error messages start with the field name ("Username must…",
// "Password needs…"), so we can put them under the right field too.
function fieldForServerError(message) {
  const m = message.toLowerCase();
  if (m.startsWith("username") || m.includes("username is already taken")) return "username";
  if (m.includes("email")) return "email";
  if (m.startsWith("password")) return "password";
  return null;
}

// Disable the button while a request is running, so a double-click
// can't create two accounts or send two logins.
async function submitWith(form, work) {
  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  try {
    await work();
  } catch (err) {
    const field = fieldForServerError(err.message);
    if (field && form[field]) {
      setFieldError(form, field, err.message);
      form[field].focus();
    } else {
      formError.textContent = err.message;
    }
  } finally {
    button.disabled = false;
  }
}

// ---------------------------------------------------------------------------
// Log in
// ---------------------------------------------------------------------------

const loginForm = document.getElementById("login-form");
if (loginForm) {
  // On the login page we only check that something was typed. We don't show
  // the signup rules here - that would give hints to someone guessing.
  const loginChecks = {
    username: (f) => (f.username.value.trim() ? "" : "Please enter your username."),
    password: (f) => (f.password.value ? "" : "Please enter your password."),
  };
  loginForm.username.addEventListener("input", () => setFieldError(loginForm, "username", ""));
  loginForm.password.addEventListener("input", () => setFieldError(loginForm, "password", ""));

  loginForm.addEventListener("submit", (event) => {
    event.preventDefault(); // stop the browser doing an old-style page reload
    clearAllErrors(loginForm);
    if (!showAllErrors(loginForm, loginChecks)) return;

    const username = loginForm.username.value.trim();
    const password = loginForm.password.value;
    submitWith(loginForm, async () => {
      const data = await api("/api/login", { method: "POST", body: { username, password } });
      Session.save(data.token, data.user);
      window.location.href = "/dashboard";
    });
  });
}

// ---------------------------------------------------------------------------
// Sign up
// ---------------------------------------------------------------------------

const signupForm = document.getElementById("signup-form");
if (signupForm) {
  // The rules themselves live in Validate (api.js), shared with the dashboard.
  // The server checks them again anyway, because a browser can be bypassed.
  const signupChecks = {
    username: (f) => Validate.username(f.username.value.trim()),
    email: (f) => Validate.email(f.email.value.trim()),
    password: (f) => Validate.password(f.password.value, f.username.value.trim()),
    confirm: (f) => {
      if (!f.confirm.value) return "Please type your password again.";
      return f.confirm.value === f.password.value ? "" : "The two passwords don't match.";
    },
  };
  checkOnBlur(signupForm, signupChecks);

  signupForm.addEventListener("submit", (event) => {
    event.preventDefault();
    clearAllErrors(signupForm);
    // Show every problem at once, each under its own field.
    if (!showAllErrors(signupForm, signupChecks)) return;

    const body = {
      username: signupForm.username.value.trim(),
      email: signupForm.email.value.trim(),
      password: signupForm.password.value,
    };
    submitWith(signupForm, async () => {
      // The server answers with a session token, so the new user is
      // logged in right away instead of having to type everything again.
      const data = await api("/api/signup", { method: "POST", body });
      Session.save(data.token, data.user);
      window.location.href = "/dashboard";
    });
  });
}