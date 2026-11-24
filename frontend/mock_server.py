"""
mock_server.py
--------------
A tiny stand-in for the real backend, so the frontend can be developed and
tested before the team's Flask application server + cloud database are ready.

It is NOT the real server: users live in a Python dict and vanish on restart.
It does implement the same API contract as api_client.py expects, including
correct REST status codes, so swapping to the real server is just a matter
of pointing SCHOLAR_API_URL at it.

Run with:   python mock_server.py      (listens on http://127.0.0.1:5000)
"""

import secrets

from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

# Re-use the frontend's rules so client and server agree.
# The server must always validate: anyone can bypass the client.
from validators import EmailValidator, NewPasswordValidator, UsernameValidator

app = Flask(__name__)

# email -> {"user_id", "username", "password_hash"}
USERS: dict[str, dict] = {}
# token -> user_id  (the real server would store sessions in the DB)
SESSIONS: dict[str, int] = {}


def _issue_token(user: dict) -> dict:
    """Create a random session token and return the JSON sent to the client."""
    token = secrets.token_hex(32)
    SESSIONS[token] = user["user_id"]
    return {"user_id": user["user_id"], "username": user["username"],
            "email": user["email"], "token": token}


@app.post("/api/signup")
def signup():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not (username and email and password):
        return jsonify(error="username, email and password are required."), 400
    for validator, value in (
        (UsernameValidator(), username),
        (EmailValidator(), email),
        (NewPasswordValidator(), password),
    ):
        result = validator.validate(value)
        if not result.is_valid:
            return jsonify(error=result.failure_descriptions[0]), 400
    if email in USERS:
        return jsonify(error="An account with that email already exists."), 409

    # Never store plain passwords - only a salted hash.
    user = {
        "user_id": len(USERS) + 1,
        "username": username,
        "email": email,
        "password_hash": generate_password_hash(password),
    }
    USERS[email] = user
    return jsonify(_issue_token(user)), 201


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not (email and password):
        return jsonify(error="email and password are required."), 400

    user = USERS.get(email)
    # Same message for "no such user" and "wrong password" so attackers can't
    # find out which emails are registered.
    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify(error="Incorrect email or password."), 401

    return jsonify(_issue_token(user)), 200


if __name__ == "__main__":
    app.run(debug=True)
