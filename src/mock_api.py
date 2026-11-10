"""mock_api.py - Temporary REST API so dashboard can be built"""

from flask import Blueprint, jsonify, request


# All routes in this blueprint start with /api
mock_api = Blueprint("mock_api", __name__, url_prefix="/api")

# Sample data, kept in memory (it resets when the server restarts)
PAPERS = [
    {"id": 1, "title": "Attention Is All You Need",
     "authors": ["A. Vaswani", "N. Shazeer"], "year": 2017,
     "venue": "NeurIPS", "citations": 120000},
    {"id": 2, "title": "MapReduce: Simplified Data Processing on Large Clusters",
     "authors": ["J. Dean", "S. Ghemawat"], "year": 2004,
     "venue": "OSDI", "citations": 25000},
    {"id": 3, "title": "Borg, Omega, and Kubernetes",
     "authors": ["B. Burns", "B. Grant"], "year": 2016,
     "venue": "ACM Queue", "citations": 1400},
]

@mock_api.get("/papers")
def list_papers():
    """
    GET /api/papers?q=<text>
    Return papers whose title, authors or venue contain the search text.
    With no q, return every paper.
    """
    q = request.args.get("q", "").strip().lower()   # read ?q= from the URL

    if q:
        results = [
            p for p in PAPERS
            if q in p["title"].lower()
            or q in p["venue"].lower()
            or any(q in author.lower() for author in p["authors"])
        ]
    else:
        results = PAPERS

    return jsonify({"items": results, "total": len(results)})