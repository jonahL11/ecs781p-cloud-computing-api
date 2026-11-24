"""
dq_app.py - Entry point for the full Daily Query frontend.

This is kept separate from the team's app.py on purpose, so nobody's
original files are changed. Run this one with:  python dq_app.py

This file only serves the HTML pages. Everything the pages actually *do*
(signing up, searching, saving favourites, managing users) goes through the
JSON API in dq_api.py, so the frontend and backend stay cleanly separated.
When the real backend + database are ready, swap the mock blueprint for the
real one and the pages won't need to change.
"""

import socket

from flask import Flask, jsonify, redirect, render_template, url_for

from dq_api import dq_api

app = Flask(__name__)

# All /api/... routes live in this blueprint (see dq_api.py).
app.register_blueprint(dq_api)


@app.route("/")
def index():
    # Nobody should land on a blank page: send them to the dashboard.
    # If they aren't logged in, the dashboard's JavaScript bounces them to /login.
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET"])
def get_login():
    # Just the page. The form posts to /api/login with JavaScript.
    return render_template("login.html")


@app.route("/signup", methods=["GET"])
def get_signup():
    # Just the page. The form posts to /api/signup with JavaScript.
    return render_template("signup.html")


@app.route("/dashboard", methods=["GET"])
def dashboard():
    # One page with several views (search, library, account, users).
    # The sidebar switches between them without reloading.
    return render_template("app_dashboard.html")


@app.route("/api/health", methods=["GET"])
def health():
    # Handy on Kubernetes: the footer shows which pod answered the request,
    # so you can see the load balancer spreading traffic across replicas.
    return jsonify({"status": "ok", "served_by": socket.gethostname()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
