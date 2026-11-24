"""
app.py
------
Terminal frontend for our Google-Scholar-style app, built with Textual.

Screens:
  LoginScreen   - email + password, calls POST /api/login
  SignupScreen  - username, email, password, confirm, calls POST /api/signup
  After login: sidebar pages (navigation.py). My Favourites is in
  favourites_page.py and My Profile in profile_page.py.

Flow (matches the team's Login/Signup diagram):
  User fills in a form -> the form is validated on the client (validators.py)
  -> frontend sends a POST to the application server (api_client.py)
  -> server creates/checks the user in the relational DB
  -> server returns a session token -> frontend stores it in `app.session`
  and uses it for later requests (e.g. searching papers).

How validation behaves for the user:
  * While typing for the first time, no errors are shown (no nagging).
  * When the user leaves a field (Tab / click away) it is checked, and any
    problem appears in red under the field.
  * After that, the field is re-checked on every key press, so the error
    disappears as soon as it is fixed.
  * On submit every field is checked and the cursor jumps to the first problem.

Run with:   python app.py
Live-reload CSS while developing:   textual run --dev app.py
Open in a web browser:              textual serve app.py
"""

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Footer, Input, Label, Static

import api_client
from favourites import FavouritesStore
from navigation import DashboardScreen
import favourites_page  # noqa: F401  registers the My Favourites page with the sidebar
import profile_page  # noqa: F401  registers the My Profile page with the sidebar
from validators import (
    EMAIL_MAX,
    PASSWORD_MAX,
    USERNAME_MAX,
    EmailValidator,
    MatchValidator,
    NewPasswordValidator,
    RequiredValidator,
    UsernameValidator,
    password_strength,
)


# --------------------------------------------------------------------------- #
# Small building blocks shared by both forms
# --------------------------------------------------------------------------- #
def brand() -> ComposeResult:
    """App name + tagline shown at the top of every card."""
    yield Static("Scholar Search", id="brand")
    yield Static("Find, read and save research papers", id="tagline")


def tabs(current: str) -> ComposeResult:
    """'Log in | Sign up' switcher. `current` is "login" or "signup"."""
    with Horizontal(id="tabs"):
        yield Button("Log in", id="tab-login", classes="tab" + (" current" if current == "login" else ""))
        yield Static("│", classes="tab-divider")
        yield Button("Sign up", id="tab-signup", classes="tab" + (" current" if current == "signup" else ""))


def field(label: str, input_widget: Input) -> ComposeResult:
    """A label, an input box and an (initially hidden) error line under it."""
    yield Label(label, classes="field-label")
    yield input_widget
    yield Static("", id=f"{input_widget.id}-error", classes="field-error")


class FormScreen(Screen):
    """Behaviour shared by the login and signup screens."""

    # Subclasses set these so the shared code knows which button is "submit".
    SUBMIT_LABEL = "Submit"
    BUSY_LABEL = "Please wait…"

    def __init__(self) -> None:
        super().__init__()
        # IDs of fields the user has already visited. We only show errors for
        # these, so a fresh form isn't covered in red.
        self.touched: set[str] = set()

    # ----- per-field validation ------------------------------------------- #
    def check_field(self, input_widget: Input) -> bool:
        """Validate one field, show/hide its error line, return True if valid."""
        result = input_widget.validate(input_widget.value)  # also colours the border
        ok = result is None or result.is_valid
        message = "" if ok else result.failure_descriptions[0]
        try:
            error_line = self.query_one(f"#{input_widget.id}-error", Static)
        except NoMatches:  # screen is being closed
            return ok
        error_line.update(message)
        error_line.display = bool(message)
        return ok

    def check_all(self) -> bool:
        """Validate every field. Focus the first bad one. True if all valid."""
        first_bad = None
        for input_widget in self.query(Input):
            self.touched.add(input_widget.id)
            if not self.check_field(input_widget) and first_bad is None:
                first_bad = input_widget
        if first_bad is not None:
            first_bad.focus()
            return False
        return True

    @on(Input.Blurred)
    def field_left(self, event: Input.Blurred) -> None:
        """User moved out of a field: check it from now on."""
        self.touched.add(event.input.id)
        self.check_field(event.input)

    @on(Input.Changed)
    def field_changed(self, event: Input.Changed) -> None:
        """Re-check visited fields on every key press so errors clear instantly."""
        if event.input.id in self.touched:
            self.check_field(event.input)

    @on(Input.Submitted)
    def enter_pressed(self, event: Input.Submitted) -> None:
        """Enter moves to the next box; on the last box it submits the form."""
        inputs = list(self.query(Input))
        if event.input is inputs[-1]:
            self.submit()
        else:
            self.focus_next(Input)

    @on(Checkbox.Changed, "#show-password")
    def toggle_password(self, event: Checkbox.Changed) -> None:
        """Show or hide every password box on this screen."""
        for input_widget in self.query("Input.secret"):
            input_widget.password = not event.value

    # ----- banner message + busy state ------------------------------------ #
    def show_message(self, text: str, kind: str = "error") -> None:
        """Show a coloured banner above the submit button ("" hides it)."""
        message = self.query_one("#message", Static)
        message.set_classes(kind)  # "error" or "success" -> coloured in styles.tcss
        message.update(text)
        message.display = bool(text)

    def set_busy(self, busy: bool) -> None:
        """Disable the submit button while waiting for the server (no double clicks)."""
        button = self.query_one("#submit", Button)
        button.disabled = busy
        button.label = self.BUSY_LABEL if busy else self.SUBMIT_LABEL

    def on_failure(self, message: str) -> None:
        """Called (on the UI thread) when the server rejects the request."""
        self.set_busy(False)
        self.show_message(message)

    # ----- switching between Log in / Sign up ----------------------------- #
    @on(Button.Pressed, "#tab-login")
    def goto_login(self) -> None:
        if not isinstance(self, LoginScreen):
            self.app.switch_screen(LoginScreen())

    @on(Button.Pressed, "#tab-signup")
    def goto_signup(self) -> None:
        if not isinstance(self, SignupScreen):
            self.app.switch_screen(SignupScreen())

    @on(Button.Pressed, "#submit")
    def submit_pressed(self) -> None:
        self.submit()

    def submit(self) -> None:  # implemented by each form
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Login
# --------------------------------------------------------------------------- #
class LoginScreen(FormScreen):
    """Email + password login form."""

    SUBMIT_LABEL = "Log in"
    BUSY_LABEL = "Logging in…"

    def compose(self) -> ComposeResult:
        with Vertical(id="card") as card:
            card.border_title = "Welcome back"
            yield from brand()
            yield from tabs("login")

            yield from field("Email", Input(
                placeholder="you@example.com",
                id="email",
                max_length=EMAIL_MAX,
                validators=[EmailValidator()],
                validate_on=["submitted"],  # we trigger checks ourselves (see FormScreen)
            ))
            yield from field("Password", Input(
                placeholder="Your password",
                password=True,
                id="password",
                classes="secret",
                max_length=PASSWORD_MAX,
                validators=[RequiredValidator("Password")],
                validate_on=["submitted"],
            ))
            yield Checkbox("Show password", id="show-password")

            yield Static("", id="message")
            yield Button(self.SUBMIT_LABEL, variant="primary", id="submit")
        yield Footer()

    def on_mount(self) -> None:
        # Put the cursor in the first box so the user can start typing straight away.
        self.query_one("#email", Input).focus()

    def submit(self) -> None:
        self.show_message("")
        if not self.check_all():
            return
        email = self.query_one("#email", Input).value.strip().lower()
        password = self.query_one("#password", Input).value
        self.set_busy(True)
        self.send_login(email, password)

    # thread=True runs the network call in the background so the UI never freezes.
    @work(thread=True, exclusive=True)
    def send_login(self, email: str, password: str) -> None:
        try:
            data = api_client.login(email, password)
        except api_client.ApiError as err:
            # UI changes must happen on the main thread, hence call_from_thread.
            self.app.call_from_thread(self.on_failure, err.message)
        else:
            self.app.call_from_thread(self.app.start_session, data)

    def on_failure(self, message: str) -> None:
        super().on_failure(message)
        # Clear the password after a failed login, like most websites do.
        password = self.query_one("#password", Input)
        password.value = ""
        password.focus()


# --------------------------------------------------------------------------- #
# Signup
# --------------------------------------------------------------------------- #
class SignupScreen(FormScreen):
    """New account form."""

    SUBMIT_LABEL = "Create account"
    BUSY_LABEL = "Creating account…"

    def compose(self) -> ComposeResult:
        with Vertical(id="card") as card:
            card.border_title = "Create an account"
            yield from brand()
            yield from tabs("signup")

            yield from field("Username", Input(
                placeholder="e.g. ada_lovelace",
                id="username",
                max_length=USERNAME_MAX,
                validators=[UsernameValidator()],
                validate_on=["submitted"],
            ))
            yield from field("Email", Input(
                placeholder="you@example.com",
                id="email",
                max_length=EMAIL_MAX,
                validators=[EmailValidator()],
                validate_on=["submitted"],
            ))

            # Password label shares its row with the live strength meter.
            with Horizontal(classes="label-row"):
                yield Label("Password", classes="field-label")
                yield Static("", id="strength")
            yield Input(
                placeholder="8+ chars with upper, lower & a number",
                password=True,
                id="password",
                classes="secret",
                max_length=PASSWORD_MAX,
                validators=[NewPasswordValidator()],
                validate_on=["submitted"],
            )
            yield Static("", id="password-error", classes="field-error")

            yield from field("Confirm password", Input(
                placeholder="Type it again",
                password=True,
                id="confirm",
                classes="secret",
                max_length=PASSWORD_MAX,
                validators=[MatchValidator(self.current_password, "Passwords don't match.")],
                validate_on=["submitted"],
            ))
            yield Checkbox("Show passwords", id="show-password")

            yield Static("", id="message")
            yield Button(self.SUBMIT_LABEL, variant="primary", id="submit")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#username", Input).focus()

    def current_password(self) -> str:
        """Used by MatchValidator to read the password box."""
        return self.query_one("#password", Input).value

    @on(Input.Changed, "#password")
    def password_changed(self, event: Input.Changed) -> None:
        """Update the strength meter, and re-check 'confirm' if already visited."""
        score, label = password_strength(event.value)
        meter = self.query_one("#strength", Static)
        meter.update(f"{'■' * score}{'□' * (4 - score)}  {label}" if label else "")
        meter.set_classes(f"s{score}")  # s0..s4 -> colour in styles.tcss
        if "confirm" in self.touched:
            self.check_field(self.query_one("#confirm", Input))

    def submit(self) -> None:
        self.show_message("")
        if not self.check_all():
            return
        username = self.query_one("#username", Input).value.strip()
        email = self.query_one("#email", Input).value.strip().lower()
        password = self.query_one("#password", Input).value
        self.set_busy(True)
        self.send_signup(username, email, password)

    @work(thread=True, exclusive=True)
    def send_signup(self, username: str, email: str, password: str) -> None:
        try:
            data = api_client.signup(username, email, password)
        except api_client.ApiError as err:
            self.app.call_from_thread(self.on_failure, err.message)
        else:
            self.app.call_from_thread(self.app.start_session, data)


# --------------------------------------------------------------------------- #
# The application
# --------------------------------------------------------------------------- #
class ScholarApp(App):
    """Entry point. Holds the session token for the whole app."""

    TITLE = "Scholar Search"
    CSS_PATH = "styles.tcss"
    BINDINGS = [("ctrl+q", "quit", "Quit")]

    def __init__(self) -> None:
        super().__init__()
        # Filled in after login/signup: {"user_id": ..., "username": ..., "token": ...}
        # Later requests send the token in an "Authorization: Bearer <token>" header.
        self.session: dict = {}
        # Temporary local favourites (see favourites.py) until the backend has them.
        self.favourites = FavouritesStore()

    def on_mount(self) -> None:
        # Built-in colour theme. Try others with Ctrl+P -> "Change theme".
        self.theme = "tokyo-night"
        self.push_screen(LoginScreen())

    def start_session(self, data: dict) -> None:
        """Called after a successful login or signup."""
        self.session = data
        self.notify(f"Logged in as {data.get('username', 'user')}", title="Welcome")
        self.switch_screen(DashboardScreen())

    def end_session(self) -> None:
        self.session = {}
        self.notify("You have been logged out.")
        self.switch_screen(LoginScreen())


if __name__ == "__main__":
    ScholarApp().run()
