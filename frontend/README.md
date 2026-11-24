# Scholar Search – Terminal Frontend

A terminal user interface (TUI) for our Google-Scholar-style cloud app, built
with [Textual](https://textual.textualize.io/) in Python. Users can sign up,
log in, and (next) search research papers. The frontend talks to the Flask
application server over its REST API.

## How it fits the architecture

```
User ──> Textual frontend ──POST /api/signup or /api/login──> Flask app server ──> Cloud relational DB
              ^                                                     │
              └──────────────── session token (JSON) ───────────────┘
```

After login/signup the token is kept in memory (`app.session`) and will be
sent as `Authorization: Bearer <token>` on later requests such as search.

## Files

| File | What it does |
|------|--------------|
| `app.py` | Entry point: Login and Signup screens, session handling |
| `api_client.py` | Every HTTP call to the backend lives here |
| `navigation.py` | Sidebar (Dashboard, Search Papers, My Favourites, My Profile, Logout) and simple Dashboard / Search Papers pages |
| `favourites_page.py` | My Favourites page: saved papers, Remove button, empty state |
| `profile_page.py` | My Profile page: account details, activity, edit username |
| `paper_card.py` | Reusable paper widget with the ☆/★ favourite toggle |
| `favourites.py` | Temporary in-memory favourites store (to be replaced by the favourites REST API) |
| `sample_papers.py` | Temporary local paper data for testing favourites |
| `validators.py` | Login/signup validation rules (username, email, password strength, matching passwords) |
| `styles.tcss` | Layout and colours (Textual CSS) |
| `mock_server.py` | Fake backend for testing the UI before the real server is ready |
| `requirements.txt` | Python dependencies |

## API contract used

| Endpoint | Body | Success | Errors |
|----------|------|---------|--------|
| `POST /api/signup` | `username`, `email`, `password` | `201` + `{user_id, username, token}` | `400` invalid input, `409` email taken |
| `POST /api/login` | `email`, `password` | `200` + `{user_id, username, token}` | `400` missing fields, `401` wrong credentials |

Errors are returned as `{"error": "message"}` and shown to the user.

## Running it

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Terminal 1 – fake backend (skip once the real server is up)
python mock_server.py

# Terminal 2 – the frontend
python app.py
```

To point the frontend at the real/deployed server:

```bash
export SCHOLAR_API_URL="https://your-server.example.com"   # Windows: set SCHOLAR_API_URL=...
python app.py
```

Developer mode with live CSS reloading: `textual run --dev app.py`
(and `textual console` in another terminal to see `print`/log output).

Open it in a web browser instead of the terminal: `textual serve app.py`, then visit http://localhost:8000.

Quit with **Ctrl+Q**.

## Favourites feature and navigation

| Screen | How to get there | Status |
|--------|------------------|--------|
| My Favourites | Sidebar or **F3** | Done: saved papers (title, authors, year, citations), Remove from Favourites, empty state |
| Search Papers | Sidebar or **F2** | Lists temporary sample papers with the ☆ Save / ★ Saved toggle |
| Dashboard | Sidebar or **F1** | Welcome message and saved-paper count |
| My Profile | Sidebar or **F4** | Avatar, account details, saved-paper activity, edit username |
| Logout | Sidebar | Clears the session and returns to Log in |

On a Mac keyboard, press **fn** with the F-keys.

**Adding the star to another page:** mount `PaperCard(paper)` for each paper,
where `paper` is a dict with `id`, `title`, `authors`, `year`, `citations`.

**Replacing a starter page:** subclass `AppScreen` in your own file,
decorate it with `@page("nav-search")` (or `nav-dashboard` / `nav-profile`),
and import your module in `app.py`. See the docstring in `navigation.py`.

## Profile API (proposed for the backend)

| Method | Endpoint | Body | Success | Errors |
|--------|----------|------|---------|--------|
| `GET` | `/api/profile` | – | `200` + `{user_id, username, email}` | `401` |
| `PUT` | `/api/profile` | `{"username": "..."}` | `200` + updated profile | `400` invalid, `401`, `409` username taken |

## Favourites API (proposed for the backend)

The frontend currently keeps favourites in memory (`favourites.py`). The
backend should provide these endpoints so it can be switched over:

| Method | Endpoint | Body | Success | Errors |
|--------|----------|------|---------|--------|
| `GET` | `/api/favourites` | – | `200` + list of papers | `401` not logged in |
| `POST` | `/api/favourites` | `{"paper_id": "..."}` | `201` | `401`, `404` unknown paper, `409` already saved |
| `DELETE` | `/api/favourites/<paper_id>` | – | `204` | `401`, `404` not in favourites |

All requests send `Authorization: Bearer <token>`.

## Validation rules

| Field | Rule |
|-------|------|
| Username | 3–20 characters, letters, numbers and `_` only |
| Email | Valid format, e.g. `name@example.com` |
| Password (signup) | 8–64 characters, no spaces, at least one uppercase, one lowercase and one number |
| Confirm password | Must match the password |

The same rules run in the mock server, because the server must always validate too.
