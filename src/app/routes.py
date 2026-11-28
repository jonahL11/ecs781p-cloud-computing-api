import socket

from flask import jsonify, render_template, request

from .extensions import db
from .models import User


def hello_world():
    # Testing HTML forms
    if request.method == "POST":
        first_name = request.form.get("fname")
        last_name = request.form.get("lname")
        full_name = f"{first_name} {last_name}"
        email = request.form.get("email")
        pw = request.form.get("pw")
        user = User(fullname=full_name, email=email, password=pw)
        db.session.add(user)
        db.session.commit()
        return f"Your name is {first_name} {last_name}"
    return render_template("form.html")


def health():
    # Shows the server is running, and which server (Kubernetes pod) answered
    return jsonify(status="ok", served_by=socket.gethostname())


def register_routes(app):
    app.add_url_rule("/", view_func=hello_world, methods=["GET", "POST"])
    app.add_url_rule("/api/health", view_func=health, methods=["GET"])
