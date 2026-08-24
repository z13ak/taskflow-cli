"""SQLite persistence for tasks."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path


def get_db_path() -> Path:
    override = os.getenv("TASKFLOW_DB")
    if override:
        return Path(override)
    home_dir = Path.home() / ".taskflow"
    home_dir.mkdir(parents=True, exist_ok=True)
    return home_dir / "tasks.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'medium',
                due_date TEXT,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                completed_at TEXT
            )
            """
        )


def add_task(conn: sqlite3.Connection, text: str, priority: str, due_date: str | None) -> int:
    with conn:
        cur = conn.execute(
            "INSERT INTO tasks (text, priority, due_date) VALUES (?, ?, ?)",
            (text, priority, due_date),
        )
        return cur.lastrowid


def list_tasks(conn: sqlite3.Connection, status: str = "pending") -> list[sqlite3.Row]:
    if status == "all":
        query = "SELECT * FROM tasks ORDER BY done ASC, due_date IS NULL, due_date ASC, id ASC"
    elif status == "done":
        query = "SELECT * FROM tasks WHERE done = 1 ORDER BY completed_at DESC"
    else:
        query = "SELECT * FROM tasks WHERE done = 0 ORDER BY due_date IS NULL, due_date ASC, id ASC"
    return conn.execute(query).fetchall()


def get_task(conn: sqlite3.Connection, task_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()


def mark_done(conn: sqlite3.Connection, task_id: int) -> bool:
    with conn:
        cur = conn.execute(
            "UPDATE tasks SET done = 1, completed_at = datetime('now') WHERE id = ? AND done = 0",
            (task_id,),
        )
        return cur.rowcount > 0


def delete_task(conn: sqlite3.Connection, task_id: int) -> bool:
    with conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cur.rowcount > 0


def get_stats(conn: sqlite3.Connection) -> dict:
    total = conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]
    done = conn.execute("SELECT COUNT(*) AS c FROM tasks WHERE done = 1").fetchone()["c"]
    overdue = conn.execute(
        "SELECT COUNT(*) AS c FROM tasks WHERE done = 0 AND due_date IS NOT NULL AND due_date < date('now')"
    ).fetchone()["c"]
    by_priority = {
        row["priority"]: row["c"]
        for row in conn.execute(
            "SELECT priority, COUNT(*) AS c FROM tasks WHERE done = 0 GROUP BY priority"
        )
    }
    return {
        "total": total,
        "done": done,
        "pending": total - done,
        "overdue": overdue,
        "by_priority": by_priority,
    }
