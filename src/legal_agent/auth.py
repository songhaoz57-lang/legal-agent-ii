# -*- coding: utf-8 -*-
"""User authentication module for legal-agent-ii."""

import os
import sqlite3
import hashlib
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import jwt
import bcrypt

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "users.db"
JWT_SECRET = os.environ.get("JWT_SECRET", "legal-agent-ii-default-secret-change-me")
JWT_EXPIRE_HOURS = int(os.environ.get("JWT_EXPIRE_HOURS", "72"))


def _get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT DEFAULT '',
            is_paid INTEGER DEFAULT 0,
            paid_session_id TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def create_user(email: str, password: str, name: str = "") -> Optional[dict]:
    conn = _get_db()
    try:
        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        conn.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            (email.lower().strip(), pw_hash, name.strip()),
        )
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
        return dict(user) if user else None
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def authenticate(email: str, password: str) -> Optional[dict]:
    conn = _get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
    conn.close()
    if not user:
        return None
    if bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        return dict(user)
    return None


def get_user_by_id(user_id: int) -> Optional[dict]:
    conn = _get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_email(email: str) -> Optional[dict]:
    conn = _get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
    conn.close()
    return dict(user) if user else None


def mark_user_paid(email: str, session_id: str) -> bool:
    conn = _get_db()
    conn.execute(
        "UPDATE users SET is_paid = 1, paid_session_id = ?, updated_at = datetime('now') WHERE email = ?",
        (session_id, email.lower().strip()),
    )
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


def is_user_paid(user_id: int) -> bool:
    conn = _get_db()
    user = conn.execute("SELECT is_paid FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return bool(user and user["is_paid"])


def create_token(user_id: int, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_user_from_request(authorization: str) -> Optional[dict]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    payload = verify_token(token)
    if not payload:
        return None
    return get_user_by_id(payload["user_id"])


# Initialize on import
init_db()
