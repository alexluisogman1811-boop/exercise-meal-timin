"""SQLite helpers. All database access in the app goes through this module,
so it can later be replaced by Google Sheets or Supabase with the same
function names. Only parameterized queries are used.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Mapping

import pandas as pd

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    nickname TEXT, sex TEXT, age INTEGER, weight_kg REAL, height_cm REAL,
    activity_level TEXT, goal TEXT, exercise_type TEXT,
    start_time TEXT, duration_min INTEGER, bedtime TEXT,
    lactose_intolerance INTEGER DEFAULT 0, allergies TEXT DEFAULT '',
    target_kcal REAL, target_protein REAL, target_carb REAL, target_fat REAL,
    guardian_consent INTEGER DEFAULT 0,
    created_at TEXT, consent_at TEXT
);
CREATE TABLE IF NOT EXISTS food_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL, food_id TEXT NOT NULL, qty REAL NOT NULL,
    eaten_at TEXT NOT NULL, slot TEXT NOT NULL,
    -- nutrient snapshot at logging time, so history survives food table edits
    kcal REAL, protein_g REAL, carb_g REAL, fat_g REAL
);
CREATE TABLE IF NOT EXISTS usage_logs (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT, page TEXT, action TEXT, timestamp TEXT, duration_sec REAL
);
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    sus_q1 INTEGER, sus_q2 INTEGER, sus_q3 INTEGER, sus_q4 INTEGER, sus_q5 INTEGER,
    sus_q6 INTEGER, sus_q7 INTEGER, sus_q8 INTEGER, sus_q9 INTEGER, sus_q10 INTEGER,
    sus_score REAL, satisfaction TEXT, comment TEXT, created_at TEXT
);
-- daily_summary is computed from food_logs (a view, never stored twice)
CREATE VIEW IF NOT EXISTS daily_summary AS
SELECT l.user_id, substr(l.eaten_at, 1, 10) AS date,
       SUM(l.kcal) AS kcal_total, SUM(l.protein_g) AS protein_total,
       SUM(l.carb_g) AS carb_total, SUM(l.fat_g) AS fat_total,
       u.target_kcal AS goal_kcal, u.target_protein AS goal_protein
FROM food_logs l LEFT JOIN users u ON u.user_id = l.user_id
GROUP BY l.user_id, substr(l.eaten_at, 1, 10);
"""

PROFILE_FIELDS = [
    "nickname", "sex", "age", "weight_kg", "height_cm", "activity_level", "goal",
    "exercise_type", "start_time", "duration_min", "bedtime", "lactose_intolerance",
    "allergies", "target_kcal", "target_protein", "target_carb", "target_fat",
    "guardian_consent",
]
EXPORT_TABLES = ["users", "food_logs", "daily_summary", "usage_logs", "feedback"]


def now_iso() -> str:
    """Current local time as an ISO string (seconds precision)."""
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def connect(db_path: Path | str = config.DB_PATH) -> Iterator[sqlite3.Connection]:
    """Open a connection, commit on success and always close."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path | str = config.DB_PATH) -> None:
    """Create all tables and the view if they do not exist yet."""
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)


# --------------------------------------------------------------------------
# Users
# --------------------------------------------------------------------------
def new_user_id() -> str:
    """Random, non-identifying user id (8 hex characters)."""
    return uuid.uuid4().hex[:8]


def create_user(user_id: str, guardian_consent: bool, db_path: Path | str = config.DB_PATH) -> None:
    """Insert a user row at consent time (profile fields filled later)."""
    with connect(db_path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, guardian_consent, created_at, consent_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, int(guardian_consent), now_iso(), now_iso()),
        )


def get_user(user_id: str, db_path: Path | str = config.DB_PATH) -> dict | None:
    """Return the user row as a dict, or None. allergies becomes a list."""
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        return None
    user = dict(row)
    user["allergies"] = [a for a in (user.get("allergies") or "").split(",") if a]
    user["lactose_intolerance"] = bool(user.get("lactose_intolerance"))
    return user


def save_profile(user_id: str, profile: Mapping, db_path: Path | str = config.DB_PATH) -> None:
    """Update the profile fields of an existing user."""
    values = []
    for f in PROFILE_FIELDS:
        v = profile.get(f)
        if f == "allergies":
            v = ",".join(v or [])
        elif f in ("lactose_intolerance", "guardian_consent"):
            v = int(bool(v))
        values.append(v)
    sets = ", ".join(f"{f} = ?" for f in PROFILE_FIELDS)  # field names are constants
    with connect(db_path) as conn:
        conn.execute(f"UPDATE users SET {sets} WHERE user_id = ?", (*values, user_id))


def delete_user_data(user_id: str, db_path: Path | str = config.DB_PATH) -> None:
    """Delete every row that belongs to the user ("delete my data")."""
    with connect(db_path) as conn:
        for table in ("food_logs", "usage_logs", "feedback", "users"):
            conn.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))


# --------------------------------------------------------------------------
# Food logs
# --------------------------------------------------------------------------
def add_food_log(user_id: str, food_id: str, qty: float, eaten_at: str, slot: str,
                 nutrients: Mapping, db_path: Path | str = config.DB_PATH) -> None:
    """Insert a food log with a nutrient snapshot (kcal, protein, carb, fat)."""
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO food_logs (user_id, food_id, qty, eaten_at, slot, kcal, protein_g, carb_g, fat_g) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, food_id, qty, eaten_at, slot, nutrients["kcal"], nutrients["protein"],
             nutrients["carb"], nutrients["fat"]),
        )


def update_food_log(log_id: int, user_id: str, qty: float, slot: str, nutrients: Mapping,
                    db_path: Path | str = config.DB_PATH) -> None:
    """Change quantity / slot of one of the user's logs."""
    with connect(db_path) as conn:
        conn.execute(
            "UPDATE food_logs SET qty = ?, slot = ?, kcal = ?, protein_g = ?, carb_g = ?, fat_g = ? "
            "WHERE log_id = ? AND user_id = ?",
            (qty, slot, nutrients["kcal"], nutrients["protein"], nutrients["carb"],
             nutrients["fat"], log_id, user_id),
        )


def delete_food_log(log_id: int, user_id: str, db_path: Path | str = config.DB_PATH) -> None:
    """Delete one of the user's logs."""
    with connect(db_path) as conn:
        conn.execute("DELETE FROM food_logs WHERE log_id = ? AND user_id = ?", (log_id, user_id))


def get_food_logs(user_id: str, date: str | None = None,
                  db_path: Path | str = config.DB_PATH) -> pd.DataFrame:
    """The user's logs, optionally for one date (YYYY-MM-DD)."""
    sql = "SELECT * FROM food_logs WHERE user_id = ?"
    params: list = [user_id]
    if date:
        sql += " AND substr(eaten_at, 1, 10) = ?"
        params.append(date)
    with connect(db_path) as conn:
        return pd.read_sql_query(sql + " ORDER BY eaten_at, log_id", conn, params=params)


def get_daily_summary(user_id: str, db_path: Path | str = config.DB_PATH) -> pd.DataFrame:
    """Rows of the daily_summary view for one user."""
    with connect(db_path) as conn:
        return pd.read_sql_query(
            "SELECT * FROM daily_summary WHERE user_id = ? ORDER BY date", conn, params=[user_id])


# --------------------------------------------------------------------------
# Usage logs
# --------------------------------------------------------------------------
def log_usage(user_id: str | None, page: str, action: str,
              db_path: Path | str = config.DB_PATH) -> None:
    """Record a page view or key action.

    For a page view, the previous page view of the same user gets its
    duration_sec (time until this view) if the gap is within one session.
    """
    ts = datetime.now()
    with connect(db_path) as conn:
        if action == "view" and user_id:
            prev = conn.execute(
                "SELECT usage_id, timestamp FROM usage_logs WHERE user_id = ? AND action = 'view' "
                "ORDER BY usage_id DESC LIMIT 1", (user_id,)).fetchone()
            if prev:
                gap = (ts - datetime.fromisoformat(prev["timestamp"])).total_seconds()
                if gap <= config.SESSION_GAP_MIN * 60:
                    conn.execute("UPDATE usage_logs SET duration_sec = ? WHERE usage_id = ?",
                                 (gap, prev["usage_id"]))
        conn.execute(
            "INSERT INTO usage_logs (user_id, page, action, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, page, action, ts.isoformat(timespec="seconds")),
        )


def session_lengths(db_path: Path | str = config.DB_PATH) -> pd.DataFrame:
    """One row per usage session: user_id, start, end, minutes, events.

    A new session starts after a gap longer than config.SESSION_GAP_MIN.
    """
    with connect(db_path) as conn:
        df = pd.read_sql_query(
            "SELECT user_id, timestamp FROM usage_logs WHERE user_id IS NOT NULL "
            "ORDER BY user_id, timestamp", conn)
    if df.empty:
        return pd.DataFrame(columns=["user_id", "session", "start", "end", "minutes", "events"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    gap = df.groupby("user_id")["timestamp"].diff() > pd.Timedelta(minutes=config.SESSION_GAP_MIN)
    df["session"] = gap.groupby(df["user_id"]).cumsum()
    out = df.groupby(["user_id", "session"]).agg(
        start=("timestamp", "min"), end=("timestamp", "max"), events=("timestamp", "size")).reset_index()
    out["minutes"] = (out["end"] - out["start"]).dt.total_seconds() / 60
    return out


# --------------------------------------------------------------------------
# Feedback and export
# --------------------------------------------------------------------------
def save_feedback(user_id: str, answers: list[int], score: float, satisfaction: Mapping,
                  comment: str, db_path: Path | str = config.DB_PATH) -> None:
    """Store one SUS + satisfaction response."""
    cols = ", ".join(f"sus_q{i}" for i in range(1, 11))
    marks = ", ".join("?" for _ in range(14))
    with connect(db_path) as conn:
        conn.execute(
            f"INSERT INTO feedback (user_id, {cols}, sus_score, satisfaction, comment, created_at) "
            f"VALUES ({marks})",
            (user_id, *answers, score, json.dumps(dict(satisfaction), ensure_ascii=False),
             comment, now_iso()),
        )


def export_table(table: str, db_path: Path | str = config.DB_PATH) -> pd.DataFrame:
    """Whole table / view as a DataFrame (admin export). Table name is whitelisted."""
    if table not in EXPORT_TABLES:
        raise ValueError(f"unknown table {table}")
    with connect(db_path) as conn:
        return pd.read_sql_query(f"SELECT * FROM {table}", conn)
