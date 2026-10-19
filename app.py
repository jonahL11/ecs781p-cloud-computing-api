"""Flask API for the academic paper discovery application."""

from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def home():
    """Return a JSON response confirming the API is running."""
    return jsonify({"message": "Paper Discovery API is running"}), 200
