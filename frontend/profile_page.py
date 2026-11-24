"""
profile_page.py
---------------
The My Profile page.

Shows:
  * an avatar with the user's initials, their username and email
  * account details: username, email, user ID
  * activity: how many papers they've saved and the most recent ones
  * an "Edit username" form, checked with the same rules as signup

Data comes from app.session (returned by the server at login/signup) and
app.favourites. Editing the username currently updates the local session
only; when the backend is ready it becomes:

    GET /api/profile                     -> 200 {user_id, username, email}
    PUT /api/profile  {"username": ...}  -> 200 updated profile
                                            400 invalid, 409 username taken
    (each request sends  Authorization: Bearer <token>)
"""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, Static

from navigation import AppScreen, page
from validators import USERNAME_MAX, UsernameValidator


def initials(name: str) -> str:
    """'ada_lovelace' -> 'AL', 'sandy' -> 'SA'."""
    parts = [p for p in name.replace("_", " ").split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[:2].upper() or "?"


@page("nav-profile")
class ProfileScreen(AppScreen):
    PAGE_TITLE = "My Profile"

    def compose_content(self) -> ComposeResult:
        session = self.app.session
        username = session.get("username", "")
        email = session.get("email", "—")

        with VerticalScroll(id="profile"):
            # ----- header: avatar + name + email -------------------------- #
            with Horizontal(id="profile-header"):
                yield Static(initials(username), id="avatar")
                with Vertical(id="profile-name-block"):
                    yield Static(username, id="profile-name", markup=False)
                    yield Static(email, id="profile-email", markup=False)

            # ----- account details ---------------------------------------- #
            with Vertical(classes="profile-section"):
                yield Label("Account details", classes="section-title")
                yield from self.detail_row("Username", username, "detail-username")
                yield from self.detail_row("Email", email, "detail-email")
                yield from self.detail_row("User ID", str(session.get("user_id", "—")), "detail-id")

            # ----- activity ----------------------------------------------- #
            with Vertical(classes="profile-section"):
                yield Label("Activity", classes="section-title")
                yield from self.detail_row("Saved papers", "", "detail-saved")
                yield Static("", id="recent-saved", markup=False)

            # ----- edit username ------------------------------------------ #
            with Vertical(classes="profile-section"):
                yield Label("Edit username", classes="section-title")
                with Horizontal(id="edit-row"):
                    yield Input(
                        value=username,
                        placeholder="New username",
                        id="new-username",
                        max_length=USERNAME_MAX,
                        validators=[UsernameValidator()],
                        validate_on=["submitted"],
                    )
                    yield Button("Save", variant="primary", id="save-username")
                yield Static("", id="new-username-error", classes="field-error")

    @staticmethod
    def detail_row(label: str, value: str, value_id: str) -> ComposeResult:
        """One 'Label ........ value' line."""
        with Horizontal(classes="profile-row"):
            yield Static(label, classes="profile-label")
            yield Static(value, id=value_id, classes="profile-value", markup=False)

    def on_mount(self) -> None:
        self.refresh_activity()

    def refresh_activity(self) -> None:
        """Fill in the saved-papers count and the 3 most recent titles."""
        favourites = self.app.favourites.list_for(self.user_id)
        self.query_one("#detail-saved", Static).update(str(len(favourites)))
        if favourites:
            lines = "\n".join(f"★ {p['title']}" for p in favourites[:3])
            text = f"Recently saved:\n{lines}"
        else:
            text = "You haven't saved any papers yet."
        self.query_one("#recent-saved", Static).update(text)

    # ----- edit username -------------------------------------------------- #
    @on(Button.Pressed, "#save-username")
    @on(Input.Submitted, "#new-username")
    def save_username(self) -> None:
        box = self.query_one("#new-username", Input)
        error_line = self.query_one("#new-username-error", Static)

        result = box.validate(box.value)
        if result is not None and not result.is_valid:
            error_line.update(result.failure_descriptions[0])
            error_line.display = True
            return
        error_line.display = False

        new_name = box.value.strip()
        if new_name == self.app.session.get("username"):
            self.app.notify("That's already your username.", timeout=2)
            return

        # TEMPORARY: update locally. Later: PUT /api/profile via api_client.
        self.app.session["username"] = new_name
        self.query_one("#profile-name", Static).update(new_name)
        self.query_one("#detail-username", Static).update(new_name)
        self.query_one("#avatar", Static).update(initials(new_name))
        self.app.notify("Username updated", timeout=2)
