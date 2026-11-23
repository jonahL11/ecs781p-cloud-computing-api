"""
api_client.py
-------------
All HTTP communication between the Textual frontend and the Flask backend
lives in this one file. The screens in app.py never call `requests`
directly; they call the small functions below.

Why keep this separate?
  * If the backend team changes a URL or a JSON field name, only this file
    needs to change.
  * It is easy to explain in the demo video: "the UI talks to the REST API
    through api_client.py".

API contract assumed (agree this with the backend team!):

  POST /api/signup   body: {"username", "email", "password"}
      201 Created    -> {"user_id": ..., "username": ..., "token": "..."}
      400 Bad Request-> {"error": "..."}   (missing / invalid fields)
      409 Conflict   -> {"error": "..."}   (email already registered)

  POST /api/login    body: {"email", "password"}
      200 OK         -> {"user_id": ..., "username": ..., "token": "..."}
      401 Unauthorized -> {"error": "..."} (wrong email or password)

The server address defaults to the local Flask dev server, and can be
changed without editing code by setting an environment variable:

    export SCHOLAR_API_URL="https://your-deployed-app.example.com"
"""

import os

import requests

# Base URL of the backend. Override with the SCHOLAR_API_URL env variable.
BASE_URL = os.environ.get("SCHOLAR_API_URL", "http://127.0.0.1:5000").rstrip("/")

# Seconds to wait for the server before giving up.
TIMEOUT = 10


class ApiError(Exception):
    """Raised when a request fails. `message` is safe to show to the user."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.message = message
        self.status = status  # HTTP status code, or None if we never got a reply


def _post(path: str, payload: dict) -> dict:
    """Send a JSON POST request and return the decoded JSON reply.

    Raises ApiError with a friendly message on network errors or on any
    4xx/5xx response from the server.
    """
    url = f"{BASE_URL}{path}"
    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT)
    except requests.ConnectionError:
        raise ApiError(f"Can't reach the server at {BASE_URL}. Is it running?")
    except requests.Timeout:
        raise ApiError("The server took too long to respond. Try again.")

    # The backend should always answer with JSON, but don't crash if it doesn't.
    try:
        data = response.json()
    except ValueError:
        data = {}

    if response.status_code >= 400:
        # Prefer the server's own error text; fall back to a generic one.
        message = data.get("error") or f"Request failed (HTTP {response.status_code})."
        raise ApiError(message, response.status_code)

    return data


def signup(username: str, email: str, password: str) -> dict:
    """Create a new account. Returns the server's JSON (includes the token)."""
    return _post(
        "/api/signup",
        {"username": username, "email": email, "password": password},
    )


def login(email: str, password: str) -> dict:
    """Log in to an existing account. Returns the server's JSON (includes the token)."""
    return _post("/api/login", {"email": email, "password": password})
