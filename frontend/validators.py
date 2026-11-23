"""
validators.py
-------------
Input validation rules for the login and signup forms.

Each class is a Textual `Validator`: Textual calls `validate(value)` and we
return either `self.success()` or `self.failure("message for the user")`.
The screens in app.py show that message under the field and turn the box red.

Keeping the rules here (instead of inside the screens) means:
  * the rules are in one place and easy to explain in the demo,
  * the backend team can copy the same rules so client and server agree.

Remember: client-side validation is only for a nice user experience.
The server must ALWAYS validate again, because anyone can bypass a client.
"""

import re
from typing import Callable

from textual.validation import ValidationResult, Validator

# Letters, numbers and underscores only, e.g. "ada_lovelace".
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")

# A practical email check: something@something.tld with no spaces.
# (A perfect email regex doesn't exist; the server can send a confirmation
# email if it needs to be sure the address is real.)
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

USERNAME_MIN, USERNAME_MAX = 3, 20
PASSWORD_MIN, PASSWORD_MAX = 8, 64
EMAIL_MAX = 254  # maximum length allowed for an email address


class UsernameValidator(Validator):
    """3-20 characters: letters, numbers and underscores."""

    def validate(self, value: str) -> ValidationResult:
        value = value.strip()
        if not value:
            return self.failure("Username is required.")
        if len(value) < USERNAME_MIN:
            return self.failure(f"Username must be at least {USERNAME_MIN} characters.")
        if len(value) > USERNAME_MAX:
            return self.failure(f"Username must be at most {USERNAME_MAX} characters.")
        if not USERNAME_PATTERN.match(value):
            return self.failure("Use only letters, numbers and underscores (_).")
        return self.success()


class EmailValidator(Validator):
    """A well-formed email address."""

    def validate(self, value: str) -> ValidationResult:
        value = value.strip()
        if not value:
            return self.failure("Email is required.")
        if len(value) > EMAIL_MAX:
            return self.failure("That email address is too long.")
        if not EMAIL_PATTERN.match(value):
            return self.failure("Enter a valid email, e.g. name@example.com.")
        return self.success()


class RequiredValidator(Validator):
    """Field must not be empty (used for the login password)."""

    def __init__(self, field_name: str) -> None:
        super().__init__()
        self.field_name = field_name

    def validate(self, value: str) -> ValidationResult:
        if not value:
            return self.failure(f"{self.field_name} is required.")
        return self.success()


class NewPasswordValidator(Validator):
    """Rules for choosing a password at signup."""

    def validate(self, value: str) -> ValidationResult:
        if not value:
            return self.failure("Password is required.")
        if len(value) < PASSWORD_MIN:
            return self.failure(f"Password must be at least {PASSWORD_MIN} characters.")
        if len(value) > PASSWORD_MAX:
            return self.failure(f"Password must be at most {PASSWORD_MAX} characters.")
        if " " in value:
            return self.failure("Password can't contain spaces.")
        if not re.search(r"[a-z]", value):
            return self.failure("Add at least one lowercase letter.")
        if not re.search(r"[A-Z]", value):
            return self.failure("Add at least one uppercase letter.")
        if not re.search(r"[0-9]", value):
            return self.failure("Add at least one number.")
        return self.success()


class MatchValidator(Validator):
    """Value must equal another field's value (used for 'Confirm password').

    `get_other` is a function that returns the other field's current text,
    so we always compare with what is in the password box right now.
    """

    def __init__(self, get_other: Callable[[], str], message: str) -> None:
        super().__init__()
        self.get_other = get_other
        self.message = message

    def validate(self, value: str) -> ValidationResult:
        if not value:
            return self.failure("Please confirm your password.")
        if value != self.get_other():
            return self.failure(self.message)
        return self.success()


def password_strength(password: str) -> tuple[int, str]:
    """Score a password from 0 to 4 and give it a label.

    This only powers the strength meter. Whether a password is allowed is
    decided by NewPasswordValidator.
    """
    if not password:
        return 0, ""
    score = 0
    if len(password) >= PASSWORD_MIN:
        score += 1
    if len(password) >= 12:
        score += 1
    if re.search(r"[a-z]", password) and re.search(r"[A-Z]", password):
        score += 1
    if re.search(r"[0-9]", password):
        score += 1
    if re.search(r"[^A-Za-z0-9]", password):  # symbols such as ! ? # @
        score += 1
    score = min(score, 4)
    labels = ["Too weak", "Weak", "Fair", "Good", "Strong"]
    return score, labels[score]
