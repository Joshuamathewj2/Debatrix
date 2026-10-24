"""SQLite persistence for debates and their turns."""

import json
import os
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any


def _db_path() -> Path:
    return Path(os.getenv("DEBATRIX_DB", "debatrix.db"))


@contextmanager
def session() -> Iterator[sqlite3.Connection]:
    """Open a connection, commit on success, and always close it."""
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS debates("
            "id TEXT PRIMARY KEY, topic TEXT, side TEXT, persona TEXT, provider TEXT, turns TEXT, "
            "created TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_debate(topic: str, side: str, persona: str, provider: str) -> str:
    ident = str(uuid.uuid4())
    with session() as conn:
        conn.execute(
            "INSERT INTO debates(id, topic, side, persona, provider, turns) VALUES(?, ?, ?, ?, ?, ?)",
            (ident, topic, side, persona, provider, "[]"),
        )
    return ident


def get_debate(ident: str) -> dict[str, Any] | None:
    with session() as conn:
        row = conn.execute("SELECT * FROM debates WHERE id = ?", (ident,)).fetchone()
    if row is None:
        return None
    return {**dict(row), "turns": json.loads(row["turns"])}


def append_turn(ident: str, turn: dict[str, Any]) -> None:
    with session() as conn:
        row = conn.execute("SELECT turns FROM debates WHERE id = ?", (ident,)).fetchone()
        if row is None:
            return
        turns = json.loads(row["turns"])
        turns.append(turn)
        conn.execute(
            "UPDATE debates SET turns = ? WHERE id = ?",
            (json.dumps(turns, ensure_ascii=False), ident),
        )
