import os

import sqlalchemy
from sqlalchemy.engine import URL


def get_db_url(
    driver: str, user: str, password: str, host: str, port: str, name: str
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
        username=user,
        password=password,
        host=host,
        port=port,
        database=name,
    )
    return db_url


class Config:
    DB_DIALECT = os.environ.get("DB_DIALECT", "sqlite")
    DB_DRIVER = DB_DIALECT + "+pymysql"
    DB_USER = str(os.environ.get("DB_USER"))
    DB_PASS = str(os.environ.get("DB_PASS"))
    DB_HOST = str(os.environ.get("DB_HOST"))
    DB_PORT = str(os.environ.get("DB_PORT"))
    DB_NAME = str(os.environ.get("DB_NAME"))
    SQLALCHEMY_DATABASE_URI = get_db_url(
        DB_DRIVER, DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME
    )
