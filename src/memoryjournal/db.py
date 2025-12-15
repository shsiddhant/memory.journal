from __future__ import annotations
from typing import TYPE_CHECKING
import sqlite3
import typer
import click
from datetime import datetime as dt
from flask import current_app, g

if TYPE_CHECKING:
    from flask import Flask


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))


cli = typer.Typer()


@click.command("init-db")
def init_db_cmd():
    init_db()
    click.echo("Initialised the database.")


sqlite3.register_converter("timestamp", lambda d: dt.fromisoformat(d.decode()))


def init_app(app: Flask):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_cmd)
