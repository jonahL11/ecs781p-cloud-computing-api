// app.js - Everything that happens on the dashboard once you're logged in.
//
// Sections, in the same order as our architecture diagram:
//   1. Login check + top bar
//   2. Sidebar and switching between views
//   3. Searching papers
//   4. Favourites (My library)
//   5. My account (a user editing their own details)
//   6. User management (admins only)
//   7. Server info in the footer

// ===========================================================================
// 1. Login check + top bar
// ===========================================================================

// No token means nobody is logged in - go to the login page and stop here.
if (!Session.token()) {
  window.location.replace("/login");
  throw new Error("Not logged in"); // halts the rest of this script
}

function renderWhoAmI() {
  const me = Session.user();
  document.getElementById("whoami").textContent =
    me.username + (me.role === "admin" ? " · admin" : "");
}
renderWhoAmI();

document.getElementById("logout-btn").addEventListener("click", async () => {
  // Tell the server to forget the token, but log out locally even if that
  // call fails - the user clicked "Log out" and expects to be logged out.
  try { await api("/api/logout", { method: "POST" }); } catch { /* ignore */ }
  Session.clear();
  window.location.href = "/login";
});

// Only admins see the "Users" tab. (The server checks this too - hiding a
// button is just for a tidy UI, not for security.)
if (Session.isAdmin()) {
  document.getElementById("users-nav").classList.remove("hidden");
}

// ===========================================================================
// 2. Sidebar and switching between views
// ===========================================================================

const sidebar = document.getElementById("sidebar");
const overlay = document.getElementById("overlay");

function openSidebar() {
  sidebar.classList.add("open");
  overlay.classList.add("show");
}

function closeSidebar() {
  sidebar.classList.remove("open");
  overlay.classList.remove("show");
}

document.getElementById("menu-btn").addEventListener("click", openSidebar);
overlay.addEventListener("click", closeSidebar); // click outside to close
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeSidebar();
});

const views = {
  search: document.getElementById("search-view"),
  library: document.getElementById("library-view"),
  account: document.getElementById("account-view"),
  users: document.getElementById("users-view"),
};

// What to (re)load whenever a view is opened, so it always shows fresh data.
const onOpen = {
  search: () => document.getElementById("search-input").focus(),
  library: loadLibrary,
  account: loadAccount,
  users: loadUsers,
};

function showView(view) {
  if (!views[view]) view = "search";
  if (view === "users" && !Session.isAdmin()) view = "search";

  for (const name in views) {
    views[name].classList.toggle("hidden", name !== view);
  }
  document.querySelectorAll(".nav-item").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.view === view);
  });

  closeSidebar();
  onOpen[view]();
}

document.querySelectorAll(".nav-item").forEach((tab) => {
  tab.addEventListener("click", () => {
    // Put the view in the URL (#library etc.) so a refresh stays on it.
    window.location.hash = tab.dataset.view;
  });
});
window.addEventListener("hashchange", () => showView(location.hash.slice(1)));

// ===========================================================================
// 3. Searching papers
// ===========================================================================

// paperId -> paper, for everything in the user's library. Lets us show a
// filled star on search results that are already saved.
const favorites = new Map();

// Semantic Scholar sends authors as [{name: "..."}]; our old mock data used
// plain strings. Accept both so either backend works.
function authorNames(paper) {
  return (paper.authors || [])
    .map((a) => (typeof a === "string" ? a : a.name))
    .filter(Boolean);
}

// Build one <li> for a paper. Using textContent (never innerHTML) for paper
// data means a weird title can't inject HTML into our page.
function paperItem(paper) {
  const li = document.createElement("li");
  li.className = "paper";

  const body = document.createElement("div");
  body.className = "paper-body";

  // Make the title a link when we have one, otherwise plain text.
  const title = document.createElement(paper.url ? "a" : "strong");
  title.className = "paper-title";
  title.textContent = paper.title;
  if (paper.url) {
    title.href = paper.url;
    title.target = "_blank";
    title.rel = "noopener";
  }

  const meta = document.createElement("div");
  meta.className = "paper-meta";
  const citations = paper.citationCount ?? paper.citations;
  meta.textContent = [
    authorNames(paper).slice(0, 4).join(", ") + (authorNames(paper).length > 4 ? " et al." : ""),
    paper.venue,
    paper.year,
    citations != null ? "Cited by " + Number(citations).toLocaleString() : "",
  ].filter(Boolean).join(" · ");

  body.append(title, meta);

  // The star button saves or removes the paper from the library.
  const star = document.createElement("button");
  star.className = "star";
  setStar(star, favorites.has(paper.paperId));
  star.addEventListener("click", () => toggleFavorite(paper, star));

  li.append(body, star);
  return li;
}

function setStar(button, saved) {
  button.textContent = saved ? "★" : "☆";
  button.classList.toggle("saved", saved);
  button.title = saved ? "Remove from library" : "Save to library";
  button.setAttribute("aria-label", button.title);
}

function showMessage(list, text) {
  list.innerHTML = "";
  const li = document.createElement("li");
  li.className = "empty";
  li.textContent = text;
  list.appendChild(li);
}

// Each search gets a number. If an older, slower request finishes after a
// newer one, we ignore it - otherwise results could "jump back" to an old query.
let latestSearch = 0;

async function runSearch(query) {
  const list = document.getElementById("search-results");
  const count = document.getElementById("result-count");
  const searchId = ++latestSearch;

  if (!query) {
    count.textContent = "";
    showMessage(list, "Type something above to start searching.");
    return;
  }

  showMessage(list, "Searching…");
  try {
    const data = await api("/api/search?" + new URLSearchParams({ q: query }));
    if (searchId !== latestSearch) return; // a newer search has started

    list.innerHTML = "";
    if (data.items.length === 0) {
      count.textContent = "";
      showMessage(list, "No papers match your search.");
      return;
    }
    count.textContent =
      `${data.items.length} of ${Number(data.total).toLocaleString()} results` +
      (data.source === "sample" ? " (offline sample data)" : "");
    for (const paper of data.items) {
      list.appendChild(paperItem(paper));
    }
  } catch (err) {
    if (searchId !== latestSearch) return;
    count.textContent = "";
    showMessage(list, "Couldn't search: " + err.message);
  }
}

// Wait until the user stops typing for a moment before searching,
// instead of hitting the API on every single keystroke.
function debounce(fn, ms = 400) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

const searchInput = document.getElementById("search-input");
searchInput.addEventListener("input", debounce(() => runSearch(searchInput.value.trim())));

// ===========================================================================
// 4. Favourites (My library)
// ===========================================================================

async function refreshFavorites() {
  const data = await api("/api/favorites");
  favorites.clear();
  for (const paper of data.items) favorites.set(paper.paperId, paper);
}

async function toggleFavorite(paper, star) {
  const saved = favorites.has(paper.paperId);
  star.disabled = true;
  try {
    if (saved) {
      await api("/api/favorites/" + encodeURIComponent(paper.paperId), { method: "DELETE" });
      favorites.delete(paper.paperId);
      toast("Removed from your library");
    } else {
      // Only send the fields we display, not Semantic Scholar's whole object.
      const toSave = {
        paperId: paper.paperId,
        title: paper.title,
        authors: authorNames(paper),
        year: paper.year ?? null,
        venue: paper.venue || "",
        citationCount: paper.citationCount ?? paper.citations ?? null,
        url: paper.url || null,
      };
      await api("/api/favorites", { method: "PUT", body: toSave });
      favorites.set(paper.paperId, toSave);
      toast("Saved to your library");
    }
    setStar(star, !saved);

    // If we un-starred something while looking at the library, redraw it.
    if (!views.library.classList.contains("hidden")) renderLibrary();
  } catch (err) {
    toast("Couldn't update library: " + err.message);
  } finally {
    star.disabled = false;
  }
}

function renderLibrary() {
  const list = document.getElementById("library-list");
  list.innerHTML = "";
  if (favorites.size === 0) {
    showMessage(list, "Nothing saved yet. Star a paper in Search to keep it here.");
    return;
  }
  for (const paper of favorites.values()) list.appendChild(paperItem(paper));
}

async function loadLibrary() {
  const list = document.getElementById("library-list");
  showMessage(list, "Loading…");
  try {
    await refreshFavorites();
    renderLibrary();
  } catch (err) {
    showMessage(list, "Couldn't load your library: " + err.message);
  }
}

// ===========================================================================
// 5. My account
// ===========================================================================
// Two separate forms: "Your details" (username + email) and "Change password"
// (current password, new password, confirm). Errors appear in red under the
// field they belong to, and only when something is actually wrong.

const accountForm = document.getElementById("account-form");
const accountError = document.getElementById("account-error");
const passwordForm = document.getElementById("password-form");
const passwordError = document.getElementById("password-error");

// Show (or clear, with "") the red message under one field.
function setFieldError(form, name, message) {
  const input = form[name];
  const slot = form.querySelector(`[data-error-for="${name}"]`);
  if (slot) slot.textContent = message || "";
  if (message) input.setAttribute("aria-invalid", "true");
  else input.removeAttribute("aria-invalid");
}

function clearFieldErrors(form) {
  form.querySelectorAll("[data-error-for]").forEach((slot) =>
    setFieldError(form, slot.dataset.errorFor, ""));
}

// Run every check, show each error under its field, focus the first bad one.
// Returns true if everything passed.
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

// Check a field when the user leaves it; clear its error as soon as they type.
function checkOnBlur(form, checks) {
  for (const [name, check] of Object.entries(checks)) {
    const input = form[name];
    input.addEventListener("blur", () => {
      if (input.value) setFieldError(form, name, check(form));
    });
    input.addEventListener("input", () => setFieldError(form, name, ""));
  }
}

// Disable the button while saving so a double-click can't send twice.
async function whileSaving(form, work) {
  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  try { await work(); } finally { button.disabled = false; }
}

// --- Your details ----------------------------------------------------------

const detailChecks = {
  username: (f) => Validate.username(f.username.value.trim()),
  email: (f) => Validate.email(f.email.value.trim()),
};
checkOnBlur(accountForm, detailChecks);

async function loadAccount() {
  accountError.textContent = "";
  clearFieldErrors(accountForm);
  resetPasswordForm();
  try {
    // GET first so the form shows what's really stored, then PUT on save.
    const me = await api("/api/users/" + Session.user().id);
    accountForm.username.value = me.username;
    accountForm.email.value = me.email;
  } catch (err) {
    accountError.textContent = err.message;
  }
}

accountForm.addEventListener("submit", (event) => {
  event.preventDefault();
  accountError.textContent = "";
  if (!showAllErrors(accountForm, detailChecks)) return;

  const body = {
    username: accountForm.username.value.trim(),
    email: accountForm.email.value.trim(),
  };
  whileSaving(accountForm, async () => {
    try {
      // Users can only PUT their own userid - the server enforces this too.
      const updated = await api("/api/users/" + Session.user().id, { method: "PUT", body });
      Session.updateUser(updated);
      renderWhoAmI();
      toast("Your details were updated");
    } catch (err) {
      const m = err.message.toLowerCase();
      const field = m.includes("username") ? "username" : m.includes("email") ? "email" : null;
      if (field) {
        setFieldError(accountForm, field, err.message);
        accountForm[field].focus();
      } else {
        accountError.textContent = err.message;
      }
    }
  });
});

// --- Change password -------------------------------------------------------

const passwordChecks = {
  current_password: (f) => (f.current_password.value ? "" : "Please enter your current password."),
  new_password: (f) => {
    const value = f.new_password.value;
    if (!value) return "Please enter a new password.";
    const problem = Validate.password(value);
    if (problem) return problem;
    if (value === f.current_password.value) return "Your new password must be different from your current one.";
    return "";
  },
  confirm_password: (f) => {
    if (!f.confirm_password.value) return "Please type your new password again.";
    return f.confirm_password.value === f.new_password.value ? "" : "The two passwords don't match.";
  },
};
checkOnBlur(passwordForm, passwordChecks);

// "Show" / "Hide" button next to each password box.
passwordForm.querySelectorAll(".pw-toggle").forEach((button) => {
  button.addEventListener("click", () => {
    const input = button.previousElementSibling;
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    button.textContent = show ? "Hide" : "Show";
    button.setAttribute("aria-label", (show ? "Hide" : "Show") + " password");
  });
});

function resetPasswordForm() {
  passwordForm.reset();
  passwordError.textContent = "";
  clearFieldErrors(passwordForm);
  passwordForm.querySelectorAll(".pw-toggle").forEach((button) => {
    button.previousElementSibling.type = "password";
    button.textContent = "Show";
    button.setAttribute("aria-label", "Show password");
  });
}

passwordForm.addEventListener("submit", (event) => {
  event.preventDefault();
  passwordError.textContent = "";
  if (!showAllErrors(passwordForm, passwordChecks)) return;

  const body = {
    current_password: passwordForm.current_password.value,
    password: passwordForm.new_password.value,
  };
  whileSaving(passwordForm, async () => {
    try {
      await api("/api/users/" + Session.user().id, { method: "PUT", body });
      resetPasswordForm();
      toast("Your password was changed");
    } catch (err) {
      // Put the server's message under the right box when we can tell which.
      const m = err.message.toLowerCase();
      const field = m.includes("current password") ? "current_password"
        : m.includes("password") ? "new_password" : null;
      if (field) {
        setFieldError(passwordForm, field, err.message);
        passwordForm[field].focus();
      } else {
        passwordError.textContent = err.message;
      }
    }
  });
});

// ===========================================================================
// 6. User management (admins only)
// ===========================================================================

const userModal = document.getElementById("user-modal");
const userForm = document.getElementById("user-form");
const userError = document.getElementById("user-error");
const confirmModal = document.getElementById("confirm-modal");

// Any "Cancel" button inside a modal just closes that modal.
document.querySelectorAll("[data-close]").forEach((btn) =>
  btn.addEventListener("click", () => btn.closest("dialog").close())
);

async function loadUsers() {
  const tbody = document.getElementById("users-body");
  tbody.innerHTML = '<tr><td colspan="5" class="empty">Loading…</td></tr>';
  try {
    const data = await api("/api/users");
    tbody.innerHTML = "";
    for (const user of data.items) tbody.appendChild(userRow(user));
  } catch (err) {
    tbody.innerHTML = "";
    const tr = tbody.insertRow();
    const td = tr.insertCell();
    td.colSpan = 5;
    td.className = "empty";
    td.textContent = "Couldn't load users: " + err.message;
  }
}

function userRow(user) {
  const tr = document.createElement("tr");
  for (const value of [user.id, user.username, user.email]) {
    tr.insertCell().textContent = value;
  }

  const roleCell = tr.insertCell();
  const badge = document.createElement("span");
  badge.className = "badge" + (user.role === "admin" ? " badge-admin" : "");
  badge.textContent = user.role;
  roleCell.appendChild(badge);

  const actions = tr.insertCell();
  actions.className = "row-actions";

  const edit = document.createElement("button");
  edit.className = "btn btn-small";
  edit.textContent = "Edit";
  edit.addEventListener("click", () => openEditUser(user.id));
  actions.appendChild(edit);

  // An admin can't delete themselves (they'd lock themselves out).
  if (user.id !== Session.user().id) {
    const del = document.createElement("button");
    del.className = "btn btn-small btn-danger-outline";
    del.textContent = "Delete";
    del.addEventListener("click", () => confirmDelete(user));
    actions.appendChild(del);
  }
  return tr;
}

// Edit = 1) GET the user's latest details  2) PUT the changes (as in the diagram).
async function openEditUser(id) {
  userError.textContent = "";
  try {
    const user = await api("/api/users/" + id);
    userForm.id.value = user.id;
    userForm.username.value = user.username;
    userForm.email.value = user.email;
    userForm.role.value = user.role;
    userForm.password.value = "";
    userModal.showModal();
  } catch (err) {
    toast("Couldn't open user: " + err.message);
  }
}

userForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  userError.textContent = "";
  const { id, ...body } = Object.fromEntries(new FormData(userForm));
  if (!body.password) delete body.password;

  try {
    const updated = await api("/api/users/" + id, { method: "PUT", body });
    // If the admin edited their own row, keep the top bar in sync.
    if (updated.id === Session.user().id) {
      Session.updateUser(updated);
      renderWhoAmI();
    }
    userModal.close();
    toast("User updated");
    loadUsers();
  } catch (err) {
    userError.textContent = err.message;
  }
});

function confirmDelete(user) {
  document.getElementById("confirm-text").textContent =
    `This permanently removes "${user.username}" and their saved papers.`;
  confirmModal.returnValue = "";
  confirmModal.showModal();

  // The dialog's form uses method="dialog", so the clicked button's value
  // ends up in returnValue when it closes.
  confirmModal.addEventListener("close", async () => {
    if (confirmModal.returnValue !== "ok") return;
    try {
      await api("/api/users/" + user.id, { method: "DELETE" });
      toast(`Deleted ${user.username}`);
      loadUsers();
    } catch (err) {
      toast("Couldn't delete: " + err.message);
    }
  }, { once: true });
}

// ===========================================================================
// 7. Server info in the footer
// ===========================================================================

async function loadServerInfo() {
  const el = document.getElementById("served-by");
  try {
    const data = await api("/api/health");
    el.textContent = data.served_by;
  } catch {
    el.textContent = "unknown";
  }
}

// ===========================================================================
// Start-up
// ===========================================================================

loadServerInfo();

// Load favourites first so search results show the right stars straight away,
// then open whichever view is in the URL (or Search by default).
refreshFavorites()
  .catch(() => { /* the library view will show the error if it matters */ })
  .finally(() => showView(location.hash.slice(1) || "search"));