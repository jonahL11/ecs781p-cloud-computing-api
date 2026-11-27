from flask import Flask

from app import models as models
from app import routes
from config import Config

from .extensions import db

# db = SQLAlchemy()


def create_app():
    # TODO fix/define what we do with this function
    app = Flask(__name__)
    app.config.from_object(Config)
    # uses SQLAlchemy method init_app not the one in database.py
    db.init_app(app)

    with app.app_context():
        db.create_all()
        routes.register_routes(app)

    return app
