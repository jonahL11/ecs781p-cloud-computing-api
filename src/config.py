import os

import sqlalchemy
from sqlalchemy.engine import URL


def get_db_url(
    driver: str,
    name: str,
    user: str | None = None,
    password: str | None = None,
    host: str | None = None,
    port: int | None = None,
) -> sqlalchemy.engine.URL:
    """
    Constructs a SQLAlchemy engine URL, with environment variables
    :param driver: the driver name like mysql+pymysql or sqlite
    :param user: the username used for auth
    :param password: the password used for auth
    :param host: the host, i.e. IP
    :param port: the port, for MySQL for instance 3306
    :param name: name of the database like main
    :return sqlalchemy.engine.URL: a sqlalchemy engine URL
    """
    db_url = URL.create(
        drivername=driver,
        database=name,
        username=user,
        password=password,
        host=host,
        port=port,
    )
    return db_url


class Config:
    """
    A configuration class to pass parameters to the Flask application context.
    Attributes:
        DB_DIALECT: SQLAlchemy dialect
        DB_DRIVER: SQLAlchemy driver
        DB_NAME: name of the database (for sqlite the db filename)
        DB_USER: username for authentication
        DB_PASS: password for authentication
        DB_PORT: database server port
        DB_HOST: database server host
        SQLALCHEMY_DATABASE_URI: SQLAlchemy engine URL, required for Flask-SQLAlchemy to connect to database
    """

    DB_DIALECT = os.environ.get("DB_DIALECT", "sqlite")
    if DB_DIALECT == "mysql":
        DB_DRIVER = f"{DB_DIALECT}+pymysql"
        DB_USER = str(os.environ.get("DB_USER"))
        DB_PASS = str(os.environ.get("DB_PASS"))
        DB_HOST = str(os.environ.get("DB_HOST"))
        DB_PORT = int(str(os.environ.get("DB_PORT")))
        DB_NAME = str(os.environ.get("DB_NAME"))
        SQLALCHEMY_DATABASE_URI = get_db_url(
            driver=DB_DRIVER,
            name=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
        )
    else:
        DB_DRIVER = DB_DIALECT
        DB_NAME = "database.db"
        SQLALCHEMY_DATABASE_URI = get_db_url(DB_DRIVER, DB_NAME)
