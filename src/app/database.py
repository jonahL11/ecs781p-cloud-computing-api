# First function: create a new or reuse an old local .db file (SQLite) + establish connection to it
# More functions: execute SQL on connection (reads, writes, etc.)


# def get_engine(app: Flask) -> sqlalchemy.engine.Engine:
#     """
#     Creates and returns a sqlalchemy engine. When the dialect (prod) is MySQL the URL is created by get_db_url().
#     Else only the path to the dev sqlite db is used.
#     :param app: Flask app for context
#     :return engine: a sqlalchemy engine
#     """
#     db_dialect = os.environ.get("DB_DIALECT", "sqlite")
#     if db_dialect == "mysql":
#         try:
#             db_url = get_db_url(
#                 driver=db_dialect + "+pymysql",
#                 user=str(os.environ.get("DB_USER")),
#                 password=str(os.environ.get("DB_PASS")),
#                 host=str(os.environ.get("DB_HOST")),
#                 port=str(os.environ.get("DB_PORT")),
#                 name=str(os.environ.get("DB_NAME")),
#             )
#             engine = sqlalchemy.create_engine(db_url, pool_pre_ping=True)
#             app.logger.info("Engine for mysql created")
#             return engine
#         except (
#             sqlalchemy.exc.SQLAlchemyError,
#             sqlglot.errors.SqlglotError,
#             OSError,
#         ) as e:
#             app.logger.error(f"DB engine creation for mysql failed with: {e}")
#     try:
#         db_path = str(Path(app.instance_path) / "database.db")
#         db_url = URL.create(drivername="sqlite", database=db_path)
#         engine = sqlalchemy.create_engine(db_url)
#         app.logger.info("Engine for sqlite created")
#         return engine
#     except (sqlalchemy.exc.SQLAlchemyError, sqlglot.errors.SqlglotError, OSError) as e:
#         app.logger.error(f"DB engine creation for sqlite failed with: {e}")


# def get_db():
#     if "db" not in g:
#         g.db = sqlite3.connect(current_app.config["DATABASE"])
#         g.db.row_factory = sqlite3.Row  # make output more readable
#         g.db.execute("PRAGMA foreign_keys = ON")  # enabling foreign keys
#     return g.db
#
#
# def close_db(e=None):
#     db = g.pop("db", None)
#     if db is not None:
#         db.close()


# def init_db():
#     """
#     Function that initializes the database. Transpiles SQLite scripts to passed dialect using sqlglot.
#     Uses short-lived engine as the setup does not require the engine to keep running.
#     :return: None
#     """
#     db = get_engine(current_app)
#     with db.begin() as conn, open("../schema.sql") as ddl:
#         query = sqlalchemy.text(ddl.read())
#         dialect = os.environ.get("DB_DIALECT", "sqlite")
#         try:
#             if dialect == "sqlite":
#                 dbapi_conn = conn.connection
#                 current_app.logger.info(
#                     f"Initializing SQLite DB @ {db.url.render_as_string(hide_password=True)}"
#                 )
#                 dbapi_conn.execute("PRAGMA foreign_keys = ON")
#                 dbapi_conn.executescript(str(query))
#             else:
#                 current_app.logger.info(
#                     f"Transpiling SQLite script to {dialect} dialect."
#                 )
#                 transpiled_query = sqlglot.transpile(
#                     str(query), read="sqlite", write=dialect
#                 )
#                 current_app.logger.info(
#                     f"Initializing {dialect} DB @ {db.url.render_as_string(hide_password=True)}"
#                 )
#                 for substatement in transpiled_query:
#                     if substatement.strip():
#                         conn.execute(sqlalchemy.text(substatement))
#         finally:
#             db.dispose()

# @click.command("init-db")
# @with_appcontext
# def init_db_command():  # instead of initializing the db everytime the flask app starts
#     init_db()
#     click.echo("Initialized the database.")
#
#
# def init_app(app):
#     app.teardown_appcontext(close_db)
#     app.cli.add_command(init_db_command)
