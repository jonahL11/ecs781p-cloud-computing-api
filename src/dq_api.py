"""
dq_api.py - A stand-in REST API so the frontend can be built and tested
before the real backend, database and Kubernetes setup are finished.

It follows the same routes as our architecture diagram:

    Login/Signup     POST /api/signup, POST /api/login, POST /api/logout
    Searching        GET  /api/search?q=...        (forwards to Semantic Scholar)
    Favourites       PUT  /api/favorites, GET /api/favorites,
                     DELETE /api/favorites/<paperId>
    User management  GET  /api/users                (admin only)
                     GET / PUT / DELETE /api/users/<userid>
                     (a normal user may only GET/PUT their *own* userid)

Everything is kept in memory, so it all resets when the server restarts.
The backend team can replace each function body with real DB calls and keep
the same URLs and JSON shapes - then the frontend won't notice the change.
"""

import json
import re
import secrets
import urllib.parse
import urllib.request
from functools import wraps

from flask import Blueprint, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

dq_api = Blueprint("dq_api", __name__, url_prefix="/api")


# ---------------------------------------------------------------------------
# Fake "database" tables
# ---------------------------------------------------------------------------

# One admin account is created up front so the user-management screens can
# be tried straight away. Log in with  admin / admin123.
USERS = {
    1: {"id": 1, "username": "admin", "email": "admin@dailyquery.dev",
        "role": "admin", "password_hash": generate_password_hash("admin123")},
}
next_user_id = 2

TOKENS = {}      # session token -> user id
FAVORITES = {}   # user id -> {paperId: paper dict}

# Used when Semantic Scholar can't be reached (no internet, rate limit, etc.)
# so the search page always has something to show during development.
SAMPLE_PAPERS = [
    {"paperId": "gfs2003", "title": "The Google File System",
     "authors": [{"name": "S. Ghemawat"}, {"name": "H. Gobioff"}, {"name": "S. Leung"}],
     "year": 2003, "venue": "SOSP", "citationCount": 9000, "url": None},
    {"paperId": "mapreduce2004", "title": "MapReduce: Simplified Data Processing on Large Clusters",
     "authors": [{"name": "J. Dean"}, {"name": "S. Ghemawat"}],
     "year": 2004, "venue": "OSDI", "citationCount": 25000, "url": None},
    {"paperId": "borg2016", "title": "Borg, Omega, and Kubernetes",
     "authors": [{"name": "B. Burns"}, {"name": "B. Grant"}],
     "year": 2016, "venue": "ACM Queue", "citationCount": 1400, "url": None},
    {"paperId": "dynamo2007", "title": "Dynamo: Amazon's Highly Available Key-value Store",
     "authors": [{"name": "G. DeCandia"}, {"name": "D. Hastorun"}],
     "year": 2007, "venue": "SOSP", "citationCount": 7000, "url": None},
    {"paperId": "bigtable2006", "title": "Bigtable: A Distributed Storage System for Structured Data",
     "authors": [{"name": "F. Chang"}, {"name": "J. Dean"}],
     "year": 2006, "venue": "OSDI", "citationCount": 8000, "url": None},
]

SEMSCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
SEMSCHOLAR_FIELDS = "title,authors,year,venue,citationCount,url"


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def public_user(user):
    """Never send the password hash back to the browser."""
    return {k: v for k, v in user.items() if k != "password_hash"}


def error(message, status):
    return jsonify({"error": message}), status


def new_session(user):
    """Create a random session token for this user and return the login payload."""
    token = secrets.token_urlsafe(32)
    TOKENS[token] = user["id"]
    return {"token": token, "user": public_user(user)}


def login_required(fn):
    """
    Decorator: reads the 'Authorization: Bearer <token>' header the frontend
    sends, looks up who it belongs to and puts them in g.user.
    Rejects the request with 401 if the token is missing or unknown.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        token = header.removeprefix("Bearer ").strip()
        user_id = TOKENS.get(token)
        if not user_id or user_id not in USERS:
            return error("Please log in first.", 401)
        g.user = USERS[user_id]
        g.token = token
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    """Same as login_required, but the user must also be an admin."""
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if g.user["role"] != "admin":
            return error("Admins only.", 403)
        return fn(*args, **kwargs)
    return wrapper


def can_access(user_id):
    """A user can see/edit their own account; an admin can see/edit anyone's."""
    return g.user["role"] == "admin" or g.user["id"] == user_id

# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------
# Change the settings below to suit your preferences. If you do, change the
# matching numbers in static/js/api.js (the Validate object) as well, so the
# browser shows the same rules the server enforces.

USERNAME_MIN = 3          # shortest allowed username
USERNAME_MAX = 20         # longest allowed username
PASSWORD_MIN = 8          # shortest allowed password

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_username(username):
    """Return an error message, or None if the username is fine."""
    if not username:
        return "Username is required."
    if not USERNAME_MIN <= len(username) <= USERNAME_MAX:
        return f"Username must be {USERNAME_MIN}–{USERNAME_MAX} characters long."
    if not username[0].isalpha():
        return "Username must start with a letter."
    if not re.fullmatch(r"[A-Za-z0-9_.]+", username):
        return "Username can only use letters, numbers, underscores and dots."
    if ".." in username or username.endswith("."):
        return "Username can't end with a dot or have two dots in a row."
    return None


def validate_email(email):
    """Return an error message, or None if the email looks valid."""
    if not email:
        return "Email is required."
    if len(email) > 254 or not EMAIL_RE.match(email):
        return "That email address doesn't look right."
    return None


def validate_password(password, username=""):
    """Return an error message, or None if the password is strong enough.
    Rules: at least 8 characters, a capital letter and a special character.
    (username is accepted but no longer used, so existing calls keep working.)"""
    if not password:
        return "Password is required."
    if len(password) < PASSWORD_MIN:
        return f"Password must be at least {PASSWORD_MIN} characters."
    if not re.search(r"[A-Z]", password):
        return "Password needs at least one capital letter."
    if not re.search(r"[^A-Za-z0-9\s]", password):
        return "Password needs at least one special character (e.g. ! @ # ?)."
    return None


def username_taken(username, ignore_id=None):
    return any(u["username"].lower() == username.lower() and u["id"] != ignore_id
               for u in USERS.values())


# ---------------------------------------------------------------------------
# Login / Signup
# ---------------------------------------------------------------------------

@dq_api.post("/signup")
def signup():
    """Create the user, hash the password straight away, log them in."""
    global next_user_id
    body = request.get_json(silent=True) or {}
    username = str(body.get("username", "")).strip()
    email = str(body.get("email", "")).strip()
    password = str(body.get("password", ""))

        # Check each field in turn and stop at the first problem.
    problem = (validate_username(username) or validate_email(email)
               or validate_password(password, username))
    if problem:
        return error(problem, 400)
    if username_taken(username):
        return error("That username is already taken.", 409)

    user = {"id": next_user_id, "username": username, "email": email,
            "role": "user", "password_hash": generate_password_hash(password)}
    USERS[user["id"]] = user
    next_user_id += 1
    return jsonify(new_session(user)), 201


@dq_api.post("/login")
def login():
    """Check username + password and hand back a session token."""
    body = request.get_json(silent=True) or {}
    username = str(body.get("username", "")).strip()
    password = str(body.get("password", ""))

    user = next((u for u in USERS.values()
                 if u["username"].lower() == username.lower()), None)
    # Same message for "no such user" and "wrong password" so we don't leak
    # which usernames exist.
    if not user or not check_password_hash(user["password_hash"], password):
        return error("Wrong username or password.", 401)
    return jsonify(new_session(user))


@dq_api.post("/logout")
@login_required
def logout():
    TOKENS.pop(g.token, None)
    return "", 204


# ---------------------------------------------------------------------------
# Searching (forwarded to Semantic Scholar)
# ---------------------------------------------------------------------------

@dq_api.get("/search")
@login_required
def search():
    """
    GET /api/search?q=<text>
    Forwards the query to Semantic Scholar and returns {items, total, source}.
    Falls back to the local sample papers if Semantic Scholar is unreachable.
    """
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"items": [], "total": 0, "source": "none"})

    params = urllib.parse.urlencode({"query": q, "limit": 20, "fields": SEMSCHOLAR_FIELDS})
    try:
        with urllib.request.urlopen(f"{SEMSCHOLAR_URL}?{params}", timeout=6) as resp:
            data = json.load(resp)
        items = data.get("data", [])
        return jsonify({"items": items, "total": data.get("total", len(items)),
                        "source": "semanticscholar"})
    except Exception:
        # Offline, rate-limited (Semantic Scholar returns 429 quite often
        # without an API key) or any other problem: use the sample data.
        ql = q.lower()
        items = [p for p in SAMPLE_PAPERS
                 if ql in p["title"].lower() or ql in p["venue"].lower()
                 or any(ql in a["name"].lower() for a in p["authors"])]
        return jsonify({"items": items, "total": len(items), "source": "sample"})


# ---------------------------------------------------------------------------
# Favourites (saved per user)
# ---------------------------------------------------------------------------

@dq_api.get("/favorites")
@login_required
def get_favorites():
    items = list(FAVORITES.get(g.user["id"], {}).values())
    return jsonify({"items": items, "total": len(items)})


@dq_api.put("/favorites")
@login_required
def add_favorite():
    """
    PUT /api/favorites with a paper in the body. PUT is idempotent here:
    saving the same paper twice just leaves one copy.
    """
    paper = request.get_json(silent=True) or {}
    paper_id = str(paper.get("paperId", "")).strip()
    if not paper_id or not paper.get("title"):
        return error("A paper needs a paperId and a title.", 400)

    FAVORITES.setdefault(g.user["id"], {})[paper_id] = paper
    return jsonify(paper)


@dq_api.delete("/favorites/<paper_id>")
@login_required
def remove_favorite(paper_id):
    FAVORITES.get(g.user["id"], {}).pop(paper_id, None)
    return "", 204


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

@dq_api.get("/users")
@admin_required
def list_users():
    users = [public_user(u) for u in USERS.values()]
    return jsonify({"items": users, "total": len(users)})


@dq_api.get("/users/<int:user_id>")
@login_required
def get_user(user_id):
    if not can_access(user_id):
        return error("You can only view your own account.", 403)
    user = USERS.get(user_id)
    if not user:
        return error("User not found.", 404)
    return jsonify(public_user(user))


@dq_api.put("/users/<int:user_id>")
@login_required
def update_user(user_id):
    """
    Update username / email / password (and role, for admins).
    Normal users may only update their own userid - as in the diagram.
    """
    if not can_access(user_id):
        return error("You can only update your own account.", 403)
    user = USERS.get(user_id)
    if not user:
        return error("User not found.", 404)

    body = request.get_json(silent=True) or {}
    username = str(body.get("username", user["username"])).strip()
    email = str(body.get("email", user["email"])).strip()
    password = str(body.get("password") or "")
    current_password = str(body.get("current_password") or "")
    role = body.get("role", user["role"])

    # Changing your *own* password needs your current one, so someone who
    # finds you logged in can't lock you out. (An admin resetting someone
    # else's password from the Users screen doesn't need theirs.)
    # 400, not 401: the frontend treats 401 as "session expired" and logs out.
    if password and user_id == g.user["id"]:
        if not current_password:
            return error("Please enter your current password.", 400)
        if not check_password_hash(user["password_hash"], current_password):
            return error("Your current password is incorrect.", 400)
        if check_password_hash(user["password_hash"], password):
            return error("Your new password must be different from your current one.", 400)

        # Same rules as signup. The password is optional here (blank = keep it).
    problem = (validate_username(username) or validate_email(email)
               or (validate_password(password, username) if password else None))
    if problem:
        return error(problem, 400)
    if username_taken(username, ignore_id=user_id):
        return error("That username is already taken.", 409)
    if role not in ("user", "admin"):
        return error("Role must be 'user' or 'admin'.", 400)
    if role != user["role"] and g.user["role"] != "admin":
        return error("Only admins can change roles.", 403)

    # Build the new version first, then swap it in - a tiny "transaction",
    # so a failed validation never leaves a half-updated user behind.
    updated = {**user, "username": username, "email": email, "role": role}
    if password:
        updated["password_hash"] = generate_password_hash(password)
        # Log this user out everywhere else (other browsers, phones), but keep
        # the session that made the change.
        for token in [t for t, uid in TOKENS.items() if uid == user_id and t != g.token]:
            del TOKENS[token]
    USERS[user_id] = updated
    return jsonify(public_user(updated))


@dq_api.delete("/users/<int:user_id>")
@admin_required
def delete_user(user_id):
    if user_id == g.user["id"]:
        return error("You can't delete your own admin account.", 400)
    if user_id not in USERS:
        return error("User not found.", 404)

    # Clean up everything that belonged to this user.
    del USERS[user_id]
    FAVORITES.pop(user_id, None)
    for token in [t for t, uid in TOKENS.items() if uid == user_id]:
        del TOKENS[token]
    return "", 204
