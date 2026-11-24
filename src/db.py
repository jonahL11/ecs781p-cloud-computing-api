
# First function: create a new or reuse an old local .db file (SQLite) + establish connection to it
# More functions: execute SQL on connection (reads, writes, etc.)

import sqlite3
import click
from flask.cli import with_appcontext
from flask import current_app, g


def get_db():
    if 'db' not in g:                         
        g.db = sqlite3.connect(current_app.config["DATABASE"])                
        g.db.row_factory = sqlite3.Row       #make output more readable
        g.db.execute("PRAGMA foreign_keys = ON") # enabling foreign keys 
    return g.db
 
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
    


def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    db.commit()
   

@click.command('init-db')
@with_appcontext
def init_db_command():              #instead of initializing the db everytime the flask app starts
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
