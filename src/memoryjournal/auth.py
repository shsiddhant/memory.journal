from __future__ import annotations

import functools

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from memoryjournal.db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/add_journal", methods=("GET", "POST"))
def add_journal():
    if g.journal:
        return redirect(url_for("index"))
    if request.method == "POST":
        journalname = request.form["journalname"]
        password = request.form["password"]
        db = get_db()
        error = None

        if not journalname:
            error = "Journal name cannot be blank"
        elif not password:
            error = "Password cannot be blank"

        if error is None:
            try:
                db.execute(
                    "INSERT INTO journal (journalname, password) VALUES (?, ?)",
                    (journalname, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"A journal with name '{journalname}' already exists."
            else:
                flash(f"Journal '{journalname}' successfully added.", "info")
                return redirect(url_for("auth.open_journal"))

        flash(error, "error")
    return render_template("auth/add_journal.html")


@bp.route("/open_journal", methods=("GET", "POST"))
def open_journal():
    if g.journal:
        return redirect(url_for("journal.index"))
    if request.method == "POST":
        db = get_db()
        error = None
        journalname = request.form["journalname"]
        password = request.form["password"]
        journal = db.execute(
            "SELECT * FROM journal WHERE journalname = ?", (journalname,)
        ).fetchone()

        if journal is None:
            error = f"Journal with name {journalname} does not exist."
        elif not check_password_hash(journal["password"], password):
            error = "Wrong password. Please try again."

        if error is None:
            session.clear()
            session["journal_id"] = journal["id"]
            return redirect(url_for("journal.index"))
        flash(error, "error")
    return render_template("auth/open_journal.html")


import time

from .config import SESSION_TIMEOUT


@bp.before_app_request
def load_open_journal():
    journal_id = session.get("journal_id")
    last_active = session.get("last_active")

    if journal_id and last_active and time.time() - last_active > SESSION_TIMEOUT:
        flash(
            f"Session has expired after {SESSION_TIMEOUT / 60} minutes."
            " Please re-open the journal.",
            "info",
        )
        session.clear()
        g.journal = None
        return None

    if journal_id is None:
        g.journal = None
    else:
        g.journal = (
            get_db()
            .execute("SELECT * FROM journal WHERE id = ?", (journal_id,))
            .fetchone()
        )

    session["last_active"] = time.time()


@bp.route("/close_journal")
def close_journal():
    session.clear()
    return redirect(url_for("index"))


def open_journal_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.journal is None:
            return redirect(url_for("auth.open_journal"))

        return view(**kwargs)

    return wrapped_view


@bp.route("/edit_journalname", methods=("POST",))
@open_journal_required
def edit_journalname():
    new_name = request.form["new_name"]
    error = None
    if not new_name:
        error = "Journal name cannot be blank"
    if error is None:
        db = get_db()
        try:
            db.execute(
                "UPDATE journal SET journalname = ? WHERE id = ?",
                (
                    new_name,
                    g.journal["id"],
                ),
            )
            db.commit()
        except db.IntegrityError:
            error = f"A journal with name '{new_name}' already exists."
        else:
            flash("Journal name successfully changed.", "success")
            return redirect(url_for("journal.settings"))
    flash(error, "error")
    return render_template("journal/settings.html", error=error)


@bp.route("/edit_password", methods=("POST",))
@open_journal_required
def edit_password():
    new_password = request.form.get("new_password")
    current_password = request.form.get("current_password")
    confirm_new_password = request.form.get("confirm_new_password")
    db = get_db()
    error = None
    if not check_password_hash(g.journal["password"], current_password):
        error = "Wrong current password. Please try again."
    elif not new_password:
        error = "Password cannot be blank"
    elif confirm_new_password != new_password:
        error = "The new password and confirm new password fields don't match."
    if error is None:
        db.execute(
            "UPDATE journal SET password = ? WHERE id = ?",
            (
                generate_password_hash(new_password),
                g.journal["id"],
            ),
        )
        db.commit()
        flash("Journal password successfully changed.", "success")
        return redirect(url_for("journal.settings"))
    flash(error, "error")
    return render_template("journal/settings.html", error=error)


@bp.route("/delete_journal", methods=("POST",))
@open_journal_required
def delete_journal():
    password = request.form.get("password")
    error = None
    journalname = g.journal["journalname"]
    if not check_password_hash(g.journal["password"], password):
        error = "Wrong password. Please try again."

    if error is None:
        db = get_db()
        db.execute("DELETE FROM memory_tag WHERE journal_id = ?", (g.journal["id"],))
        db.execute("DELETE FROM memory WHERE journal_id = ?", (g.journal["id"],))
        db.execute("DELETE FROM journal WHERE id = ?", (g.journal["id"],))
        db.execute(
            "DELETE FROM tag WHERE id NOT IN (SELECT DISTINCT tag_id FROM memory_tag)",
        )
        db.commit()
        session.clear()
        flash(f"Journal '{journalname}' deleted.", "info")
        return redirect(url_for("index"), info=f"Journal '{journalname}' deleted.")
    else:
        flash(error, "error")
        return render_template("journal/settings.html", deletion_error=error)
