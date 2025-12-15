from __future__ import annotations

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
    #    session,
)
import markdown
from memoryjournal.auth import open_journal_required
from memoryjournal.db import get_db

bp = Blueprint("journal", __name__, url_prefix="/journal/")


@bp.route("/")
@open_journal_required
def index():
    db = get_db()
    query_all = (
        "SELECT m.id"
        " FROM memory m"
        " JOIN journal j ON m.journal_id = j.id"
        " WHERE m.journal_id = ?"
        " ORDER BY memorydate ASC"
    )
    memory_ids = db.execute(query_all, (g.journal["id"],)).fetchall()
    count = len(memory_ids)

    query = (
        "SELECT m.id, journalname, m.created, memorydate, m.title, body,"
        " t.title AS tag_title"
        " FROM memory m"
        " JOIN journal j ON m.journal_id = j.id"
        " LEFT JOIN memory_tag mt ON mt.memory_id = m.id"
        " LEFT JOIN tag t on t.id = mt.tag_id"
        " WHERE m.journal_id = ? AND m.id = ?"
    )
    if memory_ids:
        oldest_id = memory_ids[0]["id"]
        newest_id = memory_ids[-1]["id"]
        oldest = db.execute(query, (g.journal["id"], oldest_id)).fetchone()
        newest = db.execute(query, (g.journal["id"], newest_id)).fetchone()
    else:
        oldest, newest = None, None
    return render_template(
        "journal/index.html",
        count=count,
        oldest=oldest,
        newest=newest,
    )


@bp.route("/add_memory", methods=("GET", "POST"))
@open_journal_required
def add_memory():
    if request.method == "POST":
        memorydate = request.form["memorydate"]
        title = request.form["title"]
        body = request.form["body"]
        tags: str
        tags = request.form["tags"]
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        error = None
        if not memorydate:
            error = "Date is required."
        elif not title:
            error = "Title is required."
        elif not body:
            error = "Description is required."
        if error is not None:
            flash(error)
        else:
            db = get_db()
            all_tags_rows = db.execute(
                "SELECT title FROM tag",
            ).fetchall()
            all_tags = [t["title"] for t in all_tags_rows]
            cursor = db.execute(
                "INSERT INTO memory (journal_id, memorydate, title, body)"
                " VALUES (?, ?, ?, ?)",
                (g.journal["id"], memorydate, title, body),
            )
            memory_id = cursor.lastrowid
            for tag in tags_list:
                if tag not in all_tags:
                    cursor_tag = db.execute(
                        ("INSERT INTO tag (title) VALUES (?)"), (tag,)
                    )
                    tag_id = cursor_tag.lastrowid
                else:
                    tag_id = db.execute(
                        "SELECT id from tag WHERE title = ?", (tag,)
                    ).fetchone()["id"]
                db.execute(
                    "INSERT INTO memory_tag (journal_id, memory_id, tag_id)"
                    " VALUES (?, ?, ?)",
                    (g.journal["id"], memory_id, tag_id),
                )
            db.commit()
            flash("Memory added to journal.", "info")
            return redirect(url_for("journal.index"))
    return render_template("journal/add_memory.html")


@bp.route("/list_memories", methods=("GET",))
@open_journal_required
def list_memories():
    db = get_db()
    query = (
        "SELECT m.id, m.title, memorydate"
        " FROM memory m"
        " LEFT JOIN memory_tag mt ON m.id = mt.memory_id"
        " LEFT JOIN tag t ON mt.tag_id = t.id"
        " WHERE m.journal_id = ?"
    )
    query_parameters = [
        g.journal["id"],
    ]
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    tags_filter: str
    tags_filter = request.args.get("tags", "")
    tags_filter_list = [tag.strip() for tag in tags_filter.split(",") if tag.strip()]
    placeholders = ", ".join("?" * len(tags_filter_list))

    if from_date:
        query += " AND memorydate >= ?"
        query_parameters.append(from_date)
    if to_date:
        query += " AND memorydate <= ?"
        query_parameters.append(to_date)
    if tags_filter_list:
        query += f" AND t.title IN ({placeholders})"
        query_parameters.extend(tags_filter_list)
        query += " GROUP BY mt.memory_id HAVING COUNT(DISTINCT t.title) = ?"
        query_parameters.append(len(tags_filter_list))
    query += " ORDER BY memorydate DESC"
    memories = db.execute(query, query_parameters).fetchall()
    if len(memories):
        oldest = memories[-1]
        newest = memories[0]
    else:
        return render_template(
            "journal/list_memories.html",
            timeline=[],
            count=0,
            newest=None,
            oldest=None,
            from_date_current=from_date,
            to_date_current=to_date,
            tags_filter_current=tags_filter,
        )
    timeline = []
    memory_id = None
    year = None
    month = None
    date = None
    for memory in memories:
        if year != memory["memorydate"].year:
            year = memory["memorydate"].year
            year_append = year
        else:
            year_append = None

        if month != memory["memorydate"].strftime("%B"):
            month = memory["memorydate"].strftime("%B")
            month_append = month
        else:
            month_append = None
        date = memory["memorydate"].strftime("%b %d")
        title = memory["title"]
        if memory_id != memory["id"]:
            memory_id = memory["id"]
            timeline.append(
                {
                    "id": memory_id,
                    "year": year_append,
                    "month": month_append,
                    "date": date,
                    "title": title,
                }
            )
    return render_template(
        "journal/list_memories.html",
        timeline=timeline,
        count=len(timeline),
        newest=newest,
        oldest=oldest,
        from_date_current=from_date,
        to_date_current=to_date,
        tags_filter_current=tags_filter,
    )


from flask import abort


def get_memory(m_id: int, check_journal=True):
    db = get_db()
    memory = db.execute(
        (
            "SELECT m.id, m.journal_id, journalname, m.created, memorydate,"
            " title, body"
            " FROM memory m JOIN journal j on m.journal_id = j.id"
            " WHERE m.id = ?"
        ),
        (m_id,),
    ).fetchone()
    if memory is None:
        abort(404, f"Memory id {id} doesn't exist.")

    if check_journal and memory["journal_id"] != g.journal["id"]:
        abort(403)

    tags_tuple_list = db.execute(
        (
            "SELECT tag.title"
            " FROM tag"
            " JOIN memory_tag mt ON mt.tag_id = tag.id"
            " WHERE mt.memory_id = ?"
        ),
        (m_id,),
    )
    tags = list(*zip(*tags_tuple_list))
    tags_str = ", ".join(tags)
    description = markdown.markdown(memory["body"], extensions=["extra"])
    return memory, description, tags_str


@bp.route("/memory/<int:id>")
@open_journal_required
def view_memory(id):
    memory = get_memory(id)
    return render_template(
        "journal/view_memory.html",
        memory=memory[0],
        description=memory[1],
        tags=memory[2],
    )


@bp.route("/memory/<int:id>/edit", methods=("GET", "POST"))
@open_journal_required
def edit_memory(id):
    memory = get_memory(id)
    current_tags = [t.strip() for t in memory[2].split(",") if t.strip()]
    db = get_db()
    all_tags_rows = db.execute(
        "SELECT title FROM tag",
    ).fetchall()
    all_tags = [t["title"] for t in all_tags_rows]
    if request.method == "POST":
        memorydate = request.form["memorydate"]
        title = request.form["title"]
        body = request.form["body"]
        tags: str
        tags = request.form["tags"]
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        error = None
        if not memorydate:
            error = "Date is required."
        elif not title:
            error = "Title is required."
        elif not body:
            error = "Description is required."
        if error is not None:
            flash(error)
        else:
            db.execute(
                ("UPDATE memory SET memorydate = ?, title = ?, body = ? WHERE id = ?"),
                (memorydate, title, body, id),
            )
            placeholders = ", ".join("?" * len(tags_list))
            tags_to_remove_tuples = db.execute(
                (f"SELECT id FROM tag WHERE title NOT IN ({placeholders})"),
                tags_list,
            ).fetchall()
            tags_to_remove = [t["id"] for t in tags_to_remove_tuples]
            placeholders = ", ".join("?" * len(tags_to_remove))
            db.execute(
                (
                    "DELETE FROM memory_tag"
                    " WHERE memory_id = ? AND"
                    f" tag_id IN ({placeholders})"
                ),
                [id] + tags_to_remove,
            )
            db.execute(
                (
                    "DELETE FROM tag"
                    " WHERE id NOT IN (SELECT DISTINCT tag_id FROM memory_tag)"
                ),
            )
            for tag in tags_list:
                if tag not in all_tags:
                    cursor_tag = db.execute(
                        ("INSERT INTO tag (title) VALUES (?)"), (tag,)
                    )
                    tag_id = cursor_tag.lastrowid
                else:
                    tag_id = db.execute(
                        ("SELECT id from tag WHERE title = ?"), (tag,)
                    ).fetchone()["id"]
                if tag not in current_tags:
                    db.execute(
                        (
                            "INSERT INTO memory_tag (journal_id, memory_id, tag_id)"
                            " VALUES (?, ?, ?)"
                        ),
                        (g.journal["id"], id, tag_id),
                    )
            db.commit()
            flash("Memory updated.", "info")
            return redirect(url_for("journal.view_memory", id=id))
    return render_template(
        "journal/edit_memory.html",
        memory=memory[0],
        description=memory[1],
        tags=memory[2],
    )


@bp.route("/memory/<int:id>/delete", methods=("POST",))
@open_journal_required
def delete_memory(id):
    db = get_db()
    db.execute(
        ("DELETE FROM memory_tag WHERE journal_id = ? AND memory_id = ?"),
        (g.journal["id"], id),
    )
    db.execute(
        ("DELETE FROM memory WHERE journal_id = ? AND id = ?"), (g.journal["id"], id)
    )
    db.execute(
        ("DELETE FROM tag WHERE id NOT IN (SELECT DISTINCT tag_id FROM memory_tag)"),
    )
    db.commit()
    flash("Memory deleted.", "info")
    return redirect(url_for("journal.list_memories"))


@bp.route("/settings", methods=("GET", "POST"))
@open_journal_required
def settings():
    if request.method == "POST":
        if request.form.get("new_name"):
            return redirect(url_for("auth.edit_journalname"))
        if (
            request.form.get("new_password")
            and request.form.get("current_password")
            and request.form.get("confirm_new_password")
        ):
            return redirect(url_for("auth.edit_password"))
        if request.form.get("password"):
            return redirect(url_for("auth.delete_journal"))
    return render_template("journal/settings.html")
