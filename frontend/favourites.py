"""
favourites.py
-------------
TEMPORARY in-memory store for each user's favourite papers.

Favourites live only while the app is running, which is enough for testing
the screens. The methods are named after the REST calls the backend should
provide later, so swapping this class for real API calls is straightforward:

    list_for(user)       ->  GET    /api/favourites
    add(user, paper)     ->  POST   /api/favourites          body: {"paper_id": ...}
    remove(user, id)     ->  DELETE /api/favourites/<paper_id>
    (each request sends  Authorization: Bearer <token>)
"""


class FavouritesStore:
    """Keeps favourite papers per user, in the order they were saved."""

    def __init__(self) -> None:
        # user_id -> {paper_id: paper dict}. Dicts keep insertion order.
        self._by_user: dict[object, dict[str, dict]] = {}

    def _papers(self, user_id) -> dict[str, dict]:
        return self._by_user.setdefault(user_id, {})

    def list_for(self, user_id) -> list[dict]:
        """All favourites for this user, most recently saved first."""
        return list(reversed(self._papers(user_id).values()))

    def count(self, user_id) -> int:
        return len(self._papers(user_id))

    def is_favourite(self, user_id, paper_id: str) -> bool:
        return paper_id in self._papers(user_id)

    def add(self, user_id, paper: dict) -> None:
        self._papers(user_id)[paper["id"]] = paper

    def remove(self, user_id, paper_id: str) -> None:
        self._papers(user_id).pop(paper_id, None)

    def toggle(self, user_id, paper: dict) -> bool:
        """Add the paper if it isn't saved, remove it if it is.
        Returns True if the paper is now a favourite."""
        if self.is_favourite(user_id, paper["id"]):
            self.remove(user_id, paper["id"])
            return False
        self.add(user_id, paper)
        return True
