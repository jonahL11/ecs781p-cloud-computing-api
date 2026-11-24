// api.js - Shared helpers used by every page.
//
// Two jobs:
//   1. Remember who is logged in (the session token + basic user info).
//   2. Talk to our Flask API, attaching the token and turning errors into
//      readable messages, so the page scripts don't repeat that code.

const TOKEN_KEY = "dq_token";
const USER_KEY = "dq_user";

// Everything about "who is logged in" lives here.
// localStorage keeps the user logged in across page reloads and tabs.
const Session = {
  save(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  // Used after the user edits their own account, so the top bar stays correct.
  updateUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  token() {
    return localStorage.getItem(TOKEN_KEY);
  },
  user() {
    try {
      return JSON.parse(localStorage.getItem(USER_KEY));
    } catch {
      return null; // corrupted value - treat as logged out
    }
  },
  isAdmin() {
    return this.user()?.role === "admin";
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

// Call our API and get back parsed JSON (or null for empty replies like 204).
// Throws an Error with the server's own message if something goes wrong.
//
//   await api("/api/favorites")                               // GET
//   await api("/api/favorites", { method: "PUT", body: paper })
async function api(path, { method = "GET", body } = {}) {
  const headers = {};
  const token = Session.token();
  if (token) headers["Authorization"] = "Bearer " + token;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const response = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  // Some replies (e.g. DELETE -> 204) have no body, so parse carefully.
  let data = null;
  const text = await response.text();
  if (text) {
    try { data = JSON.parse(text); } catch { data = null; }
  }

  // Our token stopped working (server restarted, user deleted, logged out
  // elsewhere). Send them back to log in rather than showing broken pages.
  // We only do this if we *had* a token - a failed login is also a 401.
  if (response.status === 401 && token) {
    Session.clear();
    window.location.href = "/login";
    throw new Error("Your session has expired. Please log in again.");
  }

  if (!response.ok) {
    throw new Error(data?.error || `Request failed (${response.status})`);
  }
  return data;
}

// Show a short message at the bottom of the screen for a couple of seconds.
function toast(message) {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = message;
  el.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => el.classList.remove("show"), 2200);
}
// Validation rules, shared by the signup, account and admin forms.
// Each function returns an error message, or "" if the value is fine.
// These match the checks in dq_api.py exactly - the browser checks give
// instant feedback, the server checks are the ones that really protect us.
// If you change a rule, change it in both places.
const Validate = {
  username(username) {
    if (!username) return "Username is required.";
    if (username.length < 3 || username.length > 20) return "Username must be 3–20 characters long.";
    if (!/^[A-Za-z]/.test(username)) return "Username must start with a letter.";
    if (!/^[A-Za-z][A-Za-z0-9_.]*$/.test(username)) {
      return "Username can only use letters, numbers, underscores and dots.";
    }
    if (username.includes("..") || username.endsWith(".")) {
      return "Username can't end with a dot or have two dots in a row.";
    }
    return "";
  },

  email(email) {
    if (!email) return "Email is required.";
    if (email.length > 254 || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      return "That email address doesn't look right.";
    }
    return "";
  },

  // The password rules: 8+ characters, a capital letter and a special character.
  passwordRules: [
    { id: "length", text: "At least 8 characters", test: (p) => p.length >= 8 },
    { id: "upper", text: "A capital letter", test: (p) => /[A-Z]/.test(p) },
    { id: "symbol", text: "A special character (e.g. ! @ # ?)", test: (p) => /[^A-Za-z0-9\s]/.test(p) },
  ],

  password(password) {
    if (!password) return "Password is required.";
    if (password.length < 8) return "Password must be at least 8 characters.";
    if (!/[A-Z]/.test(password)) return "Password needs at least one capital letter.";
    if (!/[^A-Za-z0-9\s]/.test(password)) return "Password needs at least one special character (e.g. ! @ # ?).";
    return "";
  },
};