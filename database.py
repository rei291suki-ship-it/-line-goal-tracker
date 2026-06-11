import sqlite3
import os
from datetime import date, timedelta
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", "data/goals.db")


def _connect():
    Path(DB_PATH).parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                registered_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS goals (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     TEXT NOT NULL,
                text        TEXT NOT NULL,
                date        TEXT NOT NULL,
                completed   INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now')),
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        """)


def register_user(user_id: str):
    with _connect() as conn:
        conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))


def get_all_user_ids() -> list[str]:
    with _connect() as conn:
        rows = conn.execute("SELECT user_id FROM users").fetchall()
    return [row["user_id"] for row in rows]


def add_goal(user_id: str, text: str) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO goals (user_id, text, date) VALUES (?, ?, ?)",
            (user_id, text, str(date.today())),
        )
    return cursor.lastrowid


def _rows_to_goals(rows) -> list[dict]:
    return [
        {"id": row["id"], "index": i + 1, "text": row["text"], "completed": bool(row["completed"])}
        for i, row in enumerate(rows)
    ]


def get_goals_by_date(user_id: str, date_str: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, text, completed FROM goals WHERE user_id=? AND date=? ORDER BY id",
            (user_id, date_str),
        ).fetchall()
    return _rows_to_goals(rows)


def get_today_goals(user_id: str) -> list[dict]:
    return get_goals_by_date(user_id, str(date.today()))


def complete_goal(user_id: str, index: int) -> bool:
    goals = get_today_goals(user_id)
    if index < 1 or index > len(goals):
        return False
    goal_id = goals[index - 1]["id"]
    with _connect() as conn:
        conn.execute(
            "UPDATE goals SET completed=1, completed_at=datetime('now') WHERE id=?",
            (goal_id,),
        )
    return True


def get_week_goals(user_id: str) -> dict[str, list[dict]]:
    today = date.today()
    result = {}
    for i in range(7):
        day = today - timedelta(days=6 - i)
        goals = get_goals_by_date(user_id, str(day))
        if goals:
            result[day.strftime("%m/%d(%a)")] = goals
    return result
