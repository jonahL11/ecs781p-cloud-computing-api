"""
paper_card.py
-------------
PaperCard: a reusable widget that shows ONE research paper
(title, authors, publication year, citations) plus an action button.

Two modes:
    PaperCard(paper)                     -> star button ☆/★ that adds/removes
                                            the paper from favourites
    PaperCard(paper, mode="favourites")  -> "Remove from Favourites" button

FOR TEAMMATES: to get the favourite star on your own pages (e.g. search
results), just yield/mount `PaperCard(paper)` for each paper. A paper is a
dict with the keys: id, title, authors, year, citations.

The favourites themselves are stored in `app.favourites` (see favourites.py).
"""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Static


class PaperCard(Horizontal):
    """One paper with a favourite star or a remove button."""

    class Removed(Message):
        """Posted to the page when the user removes this paper from favourites,
        so the page can take the card away and update its counter."""

        def __init__(self, card: "PaperCard") -> None:
            super().__init__()
            self.card = card

    def __init__(self, paper: dict, mode: str = "star") -> None:
        super().__init__(classes="paper")
        self.paper = paper
        self.card_mode = mode  # "star" or "favourites"

    @property
    def user_id(self):
        """Favourites are kept per user, so we need the logged-in user's id."""
        return self.app.session.get("user_id")

    def compose(self) -> ComposeResult:
        paper = self.paper
        with Vertical(classes="paper-info"):
            # markup=False: titles can contain [brackets] that Textual would
            # otherwise treat as colour/style tags.
            yield Static(paper["title"], classes="paper-title", markup=False)
            yield Static(f"{paper['authors']}  ·  {paper['year']}", classes="paper-meta", markup=False)
            yield Static(f"Cited by {paper['citations']:,}", classes="paper-cites")
        if self.card_mode == "favourites":
            yield Button("Remove from Favourites", variant="error", classes="remove")
        else:
            yield Button("☆  Save", classes="fav-toggle")

    def on_mount(self) -> None:
        if self.card_mode == "star":
            self.update_star()

    def update_star(self) -> None:
        """Show ★ (saved) or ☆ (not saved), based on the favourites store."""
        saved = self.app.favourites.is_favourite(self.user_id, self.paper["id"])
        star = self.query_one(".fav-toggle", Button)
        star.label = "★  Saved" if saved else "☆  Save"
        star.set_class(saved, "saved")  # gold colour in styles.tcss
        star.tooltip = "Remove from favourites" if saved else "Add to favourites"

    @on(Button.Pressed, ".fav-toggle")
    def toggle_favourite(self, event: Button.Pressed) -> None:
        """First click adds to favourites, second click removes."""
        event.stop()  # handled here; the page doesn't need to see it
        now_saved = self.app.favourites.toggle(self.user_id, self.paper)
        self.update_star()
        self.app.notify("Added to favourites" if now_saved else "Removed from favourites",
                        timeout=2)

    @on(Button.Pressed, ".remove")
    def remove_favourite(self, event: Button.Pressed) -> None:
        event.stop()
        self.app.favourites.remove(self.user_id, self.paper["id"])
        self.post_message(self.Removed(self))
