"""
Daily Habit Tracker & Analytics
Indranil: Backend, Database & Game Logic
"""

import sqlite3
import hashlib
import os
from datetime import date, timedelta
from contextlib import contextmanager

DB_NAME = "habits.db"
XP_PER_COMPLETION = 10
STREAK_BONUS_XP = 5
VALID_STATUSES = {"Completed", "Skipped", "Missed"}

@contextmanager
def get_connection():
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    except sqlite3.Error:
        if conn is not None:
            conn.rollback()
        raise
    finally:
        if conn is not None:
            conn.close()

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                habit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                habit_name TEXT NOT NULL,
                category TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE (user_id, habit_name)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                status TEXT NOT NULL,
                xp_earned INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (habit_id) REFERENCES habits(habit_id) ON DELETE CASCADE,
                UNIQUE (habit_id, log_date),
                CHECK (status IN ('Completed', 'Skipped', 'Missed'))
            )
        """)
    return True

def _hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000).hex()

def register_user(username, password):
    username = username.strip()
    if not username or not password:
        raise ValueError("Username and password cannot be empty.")
    if len(username) > 50:
        raise ValueError("Username must be 50 characters or fewer.")
    if len(password) < 8:
        raise ValueError("Password must have at least 8 characters.")

    salt = os.urandom(16).hex()
    password_hash = _hash_password(password, salt)

    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash, password_salt) VALUES (?, ?, ?)",
                (username, password_hash, salt)
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        if "UNIQUE" in str(exc).upper():
            return None
        raise

def check_password(username, password):
    with get_connection() as conn:
        user = conn.execute(
            "SELECT user_id, password_hash, password_salt FROM users WHERE username = ?",
            (username.strip(),)
        ).fetchone()

    if user is None:
        return None

    entered_hash = _hash_password(password, user["password_salt"])
    if __import__("hmac").compare_digest(entered_hash, user["password_hash"]):
        return user["user_id"]
    return None

def add_habit(user_id, habit_name, category):
    habit_name = habit_name.strip()
    category = category.strip().title()

    if not habit_name:
        raise ValueError("Habit name cannot be empty.")
    if category not in {"Health", "Work", "Focus"}:
        raise ValueError("Category must be Health, Work, or Focus.")

    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO habits (user_id, habit_name, category) VALUES (?, ?, ?)",
                (user_id, habit_name, category)
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        if "UNIQUE" in str(exc).upper():
            return None
        raise

def get_habits(user_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT habit_id, user_id, habit_name, category, created_at FROM habits WHERE user_id = ? ORDER BY habit_id",
            (user_id,)
        ).fetchall()
    return [dict(row) for row in rows]

def get_habit_logs(habit_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT log_id, habit_id, log_date, status, xp_earned FROM habit_logs WHERE habit_id = ? ORDER BY log_date DESC",
            (habit_id,)
        ).fetchall()
    return [dict(row) for row in rows]

def get_streak(habit_id, as_of_date=None):
    if as_of_date is None:
        as_of_date = date.today()
    if isinstance(as_of_date, str):
        as_of_date = date.fromisoformat(as_of_date)

    logs = get_habit_logs(habit_id)
    if not logs:
        return 0

    status_by_date = {row["log_date"]: row["status"] for row in logs}
    current_day = as_of_date

    if status_by_date.get(current_day.isoformat()) != "Completed":
        current_day -= timedelta(days=1)

    streak = 0
    while status_by_date.get(current_day.isoformat()) == "Completed":
        streak += 1
        current_day -= timedelta(days=1)

    return streak

def log_habit_status(habit_id, status, log_date=None):
    if status not in VALID_STATUSES:
        raise ValueError("Status must be Completed, Skipped, or Missed.")
    if log_date is None:
        log_date = date.today()
    if isinstance(log_date, date):
        log_date = log_date.isoformat()

    parsed_date = date.fromisoformat(log_date)

    with get_connection() as conn:
        habit = conn.execute("SELECT habit_id FROM habits WHERE habit_id = ?", (habit_id,)).fetchone()
        if habit is None:
            raise ValueError("Habit does not exist.")

        previous_date = (parsed_date - timedelta(days=1)).isoformat()
        previous_log = conn.execute(
            "SELECT status FROM habit_logs WHERE habit_id = ? AND log_date = ?",
            (habit_id, previous_date)
        ).fetchone()

        xp_earned = 0
        if status == "Completed":
            xp_earned = XP_PER_COMPLETION
            if previous_log is not None and previous_log["status"] == "Completed":
                xp_earned += STREAK_BONUS_XP

        conn.execute("""
            INSERT INTO habit_logs (habit_id, log_date, status, xp_earned)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(habit_id, log_date)
            DO UPDATE SET status = excluded.status, xp_earned = excluded.xp_earned
            """, (habit_id, log_date, status, xp_earned)
        )
    return xp_earned

def get_total_xp(user_id):
    with get_connection() as conn:
        result = conn.execute("""
            SELECT COALESCE(SUM(hl.xp_earned), 0) AS total_xp
            FROM habits h
            LEFT JOIN habit_logs hl ON h.habit_id = hl.habit_id
            WHERE h.user_id = ?
            """, (user_id,)
        ).fetchone()
    return result["total_xp"]

def get_user_level(user_id):
    total_xp = get_total_xp(user_id)
    return (total_xp // 100) + 1

def get_user_stats(user_id):
    total_xp = get_total_xp(user_id)
    level = (total_xp // 100) + 1
    xp_in_level = total_xp % 100
    return {
        "total_xp": total_xp,
        "level": level,
        "xp_in_level": xp_in_level,
        "xp_to_next_level": 100 - xp_in_level
    }