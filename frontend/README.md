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
| `app.py` | The Textual app: Login, Signup and Home screens |
| `api_client.py` | Every HTTP call to the backend lives here |
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

## Validation rules

| Field | Rule |
|-------|------|
| Username | 3–20 characters, letters, numbers and `_` only |
| Email | Valid format, e.g. `name@example.com` |
| Password (signup) | 8–64 characters, no spaces, at least one uppercase, one lowercase and one number |
| Confirm password | Must match the password |

The same rules run in the mock server, because the server must always validate too.
