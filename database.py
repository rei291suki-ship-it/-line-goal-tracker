import sqlite3
import os
from datetime import date, timedelta
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", "goals.db")


def _connect():
    p = Path(DB_PATH)
    if p.parent != Path("."):
        p.parent.mkdir(parents=True, exist_ok=True)
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
            CREATE TABLE IF NOT EXISTS goal_records (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     TEXT NOT NULL,
                goal_index  INTEGER NOT NULL,
                date        TEXT NOT NULL,
                status      TEXT DEFAULT 'pending',
                note        TEXT,
                updated_at  TEXT DEFAULT (datetime('now')),
                UNIQUE(user_id, goal_index, date),
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


def _build_goals(records: dict) -> list[dict]:
    from goals_config import FIXED_GOALS
    return [
        {
            "index": g["index"],
            "symbol": g["symbol"],
            "category": g["category"],
            "text": g["text"],
            "status": records.get(g["index"], {}).get("status", "pending"),
            "note": records.get(g["index"], {}).get("note"),
        }
        for g in FIXED_GOALS
    ]


def _fetch_records(user_id: str, date_str: str) -> dict:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT goal_index, status, note FROM goal_records WHERE user_id=? AND date=?",
            (user_id, date_str),
        ).fetchall()
    return {row["goal_index"]: {"status": row["status"], "note": row["note"]} for row in rows}


def get_today_status(user_id: str) -> list[dict]:
    return _build_goals(_fetch_records(user_id, str(date.today())))


def get_status_by_date(user_id: str, date_str: str) -> list[dict]:
    return _build_goals(_fetch_records(user_id, date_str))


def update_goal_status(user_id: str, goal_index: int, status: str, note: str = None):
    with _connect() as conn:
        conn.execute("""
            INSERT INTO goal_records (user_id, goal_index, date, status, note)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, goal_index, date)
            DO UPDATE SET status=excluded.status, note=excluded.note, updated_at=datetime('now')
        """, (user_id, goal_index, str(date.today()), status, note))


def get_week_status(user_id: str) -> dict:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # 月曜始まり
    return {
        week_start + timedelta(days=i): get_status_by_date(user_id, str(week_start + timedelta(days=i)))
        for i in range(7)
    }
