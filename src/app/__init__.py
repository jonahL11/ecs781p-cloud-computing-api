from flask import Flask
from sqlalchemy import text

from app import models as models
from app import routes
from config import Config

from .extensions import db

SCHEMA_LOCK_NAME = "paperquery_schema_init"
SCHEMA_LOCK_TIMEOUT_S = 60


def init_schema():
    """
    Initializes schema using a lock. k8s replicas on startup may try to simultaneously execute DDL.
    The lock ensures, that the truly first process, gets to execute DDL first.
    No need to lock for sqlite connections
    """
    with db.engine.connect() as conn:
        # sqlite has no locks, but also not required in dev
        if conn.dialect.name == "sqlite":
            db.metadata.create_all(bind=conn)
            conn.commit()
            return
        # lock db for some time to execute DDL in isolation
        lock_flag = conn.execute(
            text("SELECT GET_LOCK(:name, :timeout)"),
            {"name": SCHEMA_LOCK_NAME, "timeout": SCHEMA_LOCK_TIMEOUT_S},
        ).scalar()
        if lock_flag != 1:
            raise RuntimeError("Could not acquire schema init lock")
        try:
            db.metadata.create_all(bind=conn)
        finally:
            # the lock can be released, as DDL has either failed or succeeded
            conn.execute(text("SELECT RELEASE_LOCK(:name)"), {"name": SCHEMA_LOCK_NAME})
            conn.commit()


def create_app() -> Flask:
    """
    Creates the flask app. Loads a config for context variables.
    Handles database connections, and HTTP route registration.
    :return: Flask application object
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    # uses SQLAlchemy method init_app not the one in database.py
    db.init_app(app)

    with app.app_context():
        init_schema()
        routes.register_routes(app)

    return app
