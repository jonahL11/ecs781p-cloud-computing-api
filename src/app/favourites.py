"""Saving favourite papers.

    GET    /api/favourites              list my favourite papers
    POST   /api/favourites              save a paper, body: {"paper_id": 1}
    DELETE /api/favourites/<paper_id>   remove a saved paper
"""

from flask import Blueprint, jsonify, request

from .auth import current_user_id
from .extensions import db
from .models import Papers, UserFavorites

bp = Blueprint("favourites", __name__)

@bp.get("/api/favourites")
def list_favourites():
    user_id = current_user_id()
    if user_id is None:
        return jsonify(error="Login required"), 401

    favourites = UserFavorites.query.filter_by(user_id=user_id).all()
    papers = [{"id": f.papers.id, "title": f.papers.title, "doi": f.papers.doi} for f in favourites]
    return jsonify(papers)

@bp.post("/api/favourites")
def add_favourites():
    user_id = current_user_id()
    if user_id is None:
        return jsonify(error="Login required"), 401

    data = request.get_json(silent=True) or {}
    paper_id = data.get("paper_id")
    if not isinstance(paper_id, int):
        return jsonify(error="paper_id is required"), 400
    if db.session.get(Papers, paper_id) is None:
        return jsonify(error="Paper not found"), 404
    if UserFavorites.query.filter_by(user_id=user_id, paper_id=paper_id).first():
        return jsonify(error="Already in favourites"), 409

    db.session.add(UserFavorites(user_id=user_id, paper_id=paper_id))
    db.session.commit()
    return jsonify(message="Saved"), 201


@bp.delete("/api/favourites/<int:paper_id>")
def delete_favourite(paper_id):
    user_id = current_user_id()
    if user_id is None:
        return jsonify(error="Login required"), 401

    favourite = UserFavorites.query.filter_by(user_id=user_id, paper_id=paper_id).first()
    if favourite is None:
        return jsonify(error="Favoruite not found"), 404

    db.session.delete(favourite)
    db.session.commit()
    return "", 204