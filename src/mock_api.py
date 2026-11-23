"""mock_api.py - Temporary REST API so dashboard can be built"""

from flask import Blueprint, jsonify, request, url_for


# All routes in this blueprint start with /api
mock_api = Blueprint("mock_api", __name__, url_prefix="/api")

# Sample data, kept in memory (it resets when the server restarts)
PAPERS = [
       {"id": 1, "title": "The Google File System",
     "authors": ["S. Ghemawat", "H. Gobioff", "S. Leung"], "year": 2003,
     "venue": "SOSP", "citations": 9000},
    {"id": 2, "title": "MapReduce: Simplified Data Processing on Large Clusters",
     "authors": ["J. Dean", "S. Ghemawat"], "year": 2004,
     "venue": "OSDI", "citations": 25000},
    {"id": 3, "title": "Borg, Omega, and Kubernetes",
     "authors": ["B. Burns", "B. Grant"], "year": 2016,
     "venue": "ACM Queue", "citations": 1400},
]

next_id = len(PAPERS) + 1

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

@mock_api.get("/papers/<int:paper_id>")
def get_paper(paper_id):
    """Get /api/papers/<id> - one paper, 404 if does not exist."""
    for p in PAPERS:
        if p["id"] == paper_id:
            return jsonify(p)
    return jsonify({"error": "Paper not found."}), 404
    
@mock_api.post("/papers")
def create_paper():
    """
    POST /api/papers - create a paper from JSON body.        
    """
    global next_id
    body = request.get_json(silent=True)        
    if not body or not str(body.get("title","")).strip():
        return jsonify({"error":"Title is required."}), 400
        
    try:
        year = int(body["year"]) if body.get("year") else None
        citations = int(body["citations"]) if body.get("citations") else 0 
    except ValueError:
        return jsonify({"error": "Year and citations must be numbers."}), 400
            
    authors = [a.strip() for a in str(body.get("authors", "")).split(",") if a.strip()]
    paper = {
        "id": next_id,     
        "title": body["title"].strip(),
        "authors": authors,
        "year": year,
        "venue": str(body.get("venue", "")).strip(),
        "citations": citations,
    }
    next_id += 1
    PAPERS.append(paper)

    response = jsonify(paper)
    response.status_code = 201      
    response.headers["Location"] = url_for("mock_api.get_paper", paper_id=paper["id"])
    return response



