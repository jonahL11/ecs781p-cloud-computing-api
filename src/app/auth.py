from flask import request


def authenticate(username, password):
    pass


# TEMPORARY: replace with the real login check once it exists.
def current_user_id():
    """Return the logged-in user's ID, or None. For now it reads the X-User-Id header."""
    value = request.headers.get("X-User-Id", "")
    return int(value) if value.isdigit() else None
