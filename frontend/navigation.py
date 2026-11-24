"""
navigation.py
-------------
Sidebar navigation shared by every page shown after login:

    Dashboard  |  Search Papers  |  My Favourites  |  My Profile  |  Logout

How it works
  * AppScreen is the base class for logged-in pages. It draws the sidebar on
    the left and the page's own content (compose_content) on the right.
  * Each page registers itself with @page("nav-...") so the sidebar knows
    which screen to open. Clicking an item (or F1-F4) switches screen.
  * A terminal app has no URLs, so each "page" (e.g. /favourites) is a Screen.

FOR TEAMMATES
  Dashboard and Search Papers below are simple starter pages. To build a
  fuller version, create your own screen in your own file, e.g.

      from navigation import AppScreen, page

      @page("nav-search")
      class SearchScreen(AppScreen):
          PAGE_TITLE = "Search Papers"
          def compose_content(self):
              ...

  and import your module in app.py. Registering the same nav id replaces the
  starter page, so you don't need to edit this file.
"""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Static

from paper_card import PaperCard
from sample_papers import SAMPLE_PAPERS

# nav id -> screen class. Filled in by the @page decorator.
PAGES: dict[str, type] = {}


def page(nav_id: str):
    """Class decorator: link a screen to a sidebar item."""

    def register(screen_class):
        screen_class.NAV_ID = nav_id
        PAGES[nav_id] = screen_class
        return screen_class

    return register


class Sidebar(Vertical):
    """Navigation menu shown on the left of every logged-in page."""

    ITEMS = [
        ("nav-dashboard", "⌂  Dashboard"),
        ("nav-search", "⌕  Search Papers"),
        ("nav-favourites", "★  My Favourites"),
        ("nav-profile", "☺  My Profile"),
    ]

    def __init__(self, current: str) -> None:
        super().__init__(id="sidebar")
        self.current_page = current  # nav id of the page we're on

    def compose(self) -> ComposeResult:
        yield Static("Scholar Search", id="sidebar-brand")
        for item_id, label in self.ITEMS:
            classes = "nav current" if item_id == self.current_page else "nav"
            yield Button(label, id=item_id, classes=classes)
        yield Static("", id="sidebar-spacer")  # pushes Logout to the bottom
        yield Button("⏻  Logout", id="nav-logout", classes="nav")


class AppScreen(Screen):
    """Base for logged-in pages: sidebar on the left, content on the right."""

    NAV_ID = ""      # set by @page
    PAGE_TITLE = ""  # heading at the top of the page

    BINDINGS = [
        ("f1", "go('nav-dashboard')", "Dashboard"),
        ("f2", "go('nav-search')", "Search"),
        ("f3", "go('nav-favourites')", "Favourites"),
        ("f4", "go('nav-profile')", "Profile"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="layout"):
            yield Sidebar(self.NAV_ID)
            with Vertical(id="content"):
                yield Static(self.PAGE_TITLE, id="page-title")
                yield from self.compose_content()
        yield Footer()

    def compose_content(self) -> ComposeResult:
        """Each page fills in its own content here."""
        yield from ()

    @property
    def user_id(self):
        return self.app.session.get("user_id")

    @on(Button.Pressed, ".nav")
    def nav_pressed(self, event: Button.Pressed) -> None:
        self.action_go(event.button.id)

    def action_go(self, nav_id: str) -> None:
        """Open the page for a sidebar item, or log out."""
        if nav_id == "nav-logout":
            self.app.end_session()
            return
        screen_class = PAGES.get(nav_id)
        if screen_class is not None and not isinstance(self, screen_class):
            self.app.switch_screen(screen_class())


# --------------------------------------------------------------------------- #
# Simple starter pages (to be expanded)
# --------------------------------------------------------------------------- #
@page("nav-dashboard")
class DashboardScreen(AppScreen):
    """Landing page after login."""

    PAGE_TITLE = "Dashboard"

    def compose_content(self) -> ComposeResult:
        username = self.app.session.get("username", "researcher")
        saved = self.app.favourites.count(self.user_id)
        yield Static(f"Welcome, {username}!", classes="welcome", markup=False)
        yield Static(f"You have {saved} saved paper{'' if saved == 1 else 's'}.", classes="hint")
        yield Static("Use the menu on the left to search for papers, view your "
                     "favourites or manage your profile.", classes="hint")


@page("nav-search")
class SearchScreen(AppScreen):
    """Lists the temporary sample papers so the favourite star can be tested.
    A real search (calling the backend) can replace this and reuse PaperCard
    to keep the star."""

    PAGE_TITLE = "Search Papers"

    def compose_content(self) -> ComposeResult:
        yield Static("Press ☆ Save to add a paper to My Favourites, "
                     "press it again to remove it.", classes="hint")
        with VerticalScroll(classes="paper-list"):
            for paper in SAMPLE_PAPERS:
                yield PaperCard(paper)
