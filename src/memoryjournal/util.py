from collections.abc import Iterable
from datetime import datetime
import json
import sqlite3


def get_memories_from_journal(db: sqlite3.Connection, journal_id: int):
    query = """
        SELECT DISTINCT
            m.id,
            m.created,
            m.memorydate,
            m.title,
            replace(m.body, '\r', '') as body,
            json_group_array(t.title) AS tags
        FROM memory m
        LEFT JOIN memory_tag mt
            ON mt.memory_id = m.id
        LEFT JOIN tag t
            ON t.id = mt.tag_id
        WHERE m.journal_id = ?
        GROUP BY m.id
        """
    return db.execute(query, (journal_id,)).fetchall()


def get_journal_from_id(db: sqlite3.Connection, journal_id: int):
    query = """
        SELECT
            id,
            journalname,
            created,
            modified
        FROM journal
        WHERE id = ?
        """
    return db.execute(query, (journal_id,)).fetchone()


def serialize_rows(rows: Iterable[sqlite3.Row] | sqlite3.Row):
    if isinstance(rows, sqlite3.Row):
        return {k: rows[k] for k in rows.keys()}
    elif isinstance(rows, Iterable):
        return [serialize_rows(r) for r in rows]
    else:
        raise ValueError


def export_journal(db: sqlite3.Connection, journal_id: int):
    journal = get_journal_from_id(db, journal_id)
    memories = serialize_rows(get_memories_from_journal(db, journal_id))
    for m in memories:
        if isinstance(m, dict) and "tags" in m:
            m["tags"] = json.loads(m["tags"])
        if isinstance(m, dict) and "memorydate" in m:
            m["memorydate"] = datetime.date(m["memorydate"])
    export_json = serialize_rows(journal)
    if isinstance(export_json, dict):
        export_json["memories"] = memories
        return export_json
    else:
        raise ValueError
