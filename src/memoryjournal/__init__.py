from __future__ import annotations
from typing import TYPE_CHECKING
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
import secrets
from platformdirs import user_data_path
if TYPE_CHECKING:
    from collections.abc import Mapping

from . import db, auth, journal

csrf = CSRFProtect()

def create_app(testconfig: Mapping | None = None):
    BASE_DIR = user_data_path(
        appname="memoryjournal",
        appauthor=False,
        ensure_exists=True
    )
    CONFIG_FILE = BASE_DIR / "config.py"
    DATABASE = BASE_DIR / "memoryjournal.sqlite"
    if not CONFIG_FILE.exists():
        DEFAULT_CONFIG = f"""
SESSION_TIMEOUT = 30 * 60  # 30 minutes
SECRET_KEY = '{secrets.token_hex(32)}'
"""
        CONFIG_FILE.write_text(DEFAULT_CONFIG)
    app = Flask(__name__, instance_path=str(BASE_DIR), instance_relative_config=True)
    app.config.from_mapping(DATABASE=DATABASE)
    if testconfig is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(testconfig)

    @app.route("/")
    def index():
        return render_template("index.html")

    db.init_app(app)
    with app.app_context():
        if not DATABASE.exists():
            db.init_db()
    csrf.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(journal.bp)

    @app.context_processor
    def get_journals_list():
        dba = auth.get_db()
        journals = dba.execute("SELECT id, journalname FROM journal").fetchall()
        return {"journals": journals}

    return app

