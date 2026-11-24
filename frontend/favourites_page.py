"""
favourites_page.py
------------------
The My Favourites page (the app's "/favourites" page).

  * Lists the logged-in user's saved papers: title, authors, year, citations.
  * Each paper has a "Remove from Favourites" button.
  * When nothing is saved it shows: "You haven't saved any papers yet."

Data comes from app.favourites (temporary in-memory store, see favourites.py).
"""

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static

from navigation import AppScreen, page
from paper_card import PaperCard


@page("nav-favourites")
class FavouritesScreen(AppScreen):
    PAGE_TITLE = "My Favourites"
    EMPTY_MESSAGE = "You haven't saved any papers yet."

    def compose_content(self) -> ComposeResult:
        favourites = self.app.favourites.list_for(self.user_id)

        yield Static("", id="result-count")
        with VerticalScroll(id="favourites", classes="paper-list"):
            for paper in favourites:
                yield PaperCard(paper, mode="favourites")

        # Empty state (shown or hidden by refresh_count).
        with Vertical(id="empty", classes="empty-state"):
            yield Static(self.EMPTY_MESSAGE, id="empty-title")
            yield Static("Go to Search Papers (F2) and press ☆ beside a paper to save it here.")

    def on_mount(self) -> None:
        self.refresh_count()

    def refresh_count(self) -> None:
        """Update the '3 saved papers' line and swap in the empty state at 0."""
        count = self.app.favourites.count(self.user_id)
        noun = "paper" if count == 1 else "papers"
        self.query_one("#result-count", Static).update(f"{count} saved {noun}" if count else "")
        self.query_one("#empty").display = count == 0
        self.query_one("#favourites").display = count > 0

    @on(PaperCard.Removed)
    async def paper_removed(self, event: PaperCard.Removed) -> None:
        """A card's Remove button was pressed: take the card off the page."""
        await event.card.remove()
        self.app.notify("Removed from favourites", timeout=2)
        self.refresh_count()
