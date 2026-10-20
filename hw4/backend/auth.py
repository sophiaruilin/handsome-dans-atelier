"""Password hashing, password rules, login rate limiting and sessions for Campus Customs.

Stored format (same as the seeded users): pbkdf2_sha256$<salt>$<hex hash>
- PBKDF2-HMAC-SHA256, 120,000 iterations, salt = the salt string's UTF-8 bytes.
- Sign-up and login share these settings, so a correct password always re-hashes to the stored value.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

ALGORITHM = "pbkdf2_sha256"
HASH_NAME = "sha256"
ITERATIONS = 120_000  # must match the seeded users, or their passwords stop matching
SALT_BYTES = 16       # 128-bit random salt, stored as 32 hex characters

PASSWORD_MIN = 12
PASSWORD_MAX = 128
# A short list of the most-used passwords. A production site would check a breached-password list.
COMMON_PASSWORDS = {
    "password", "password1", "password123", "123456789012", "qwertyuiop12", "iloveyou1234",
    "letmein12345", "welcome12345", "yaleyaleyale", "bulldogs1234", "boolaboola12", "passw0rd1234",
}

SESSION_COOKIE = "cc_session"
SESSION_DAYS = 7

LOGIN_MAX_FAILURES = 5
LOGIN_WINDOW_SECONDS = 15 * 60


# --- Hashing -------------------------------------------------------------------------------

def _pbkdf2(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(HASH_NAME, password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS).hex()


def hash_password(password: str) -> str:
    """Hash a new password with a fresh random salt (sign-up only)."""
    salt = secrets.token_hex(SALT_BYTES)
    return f"{ALGORITHM}${salt}${_pbkdf2(password, salt)}"


def verify_password(password: str, stored: str) -> bool:
    """Re-hash the typed password with the stored salt and compare in constant time. Never un-hashes."""
    try:
        algorithm, salt, expected = stored.split("$")
    except ValueError:
        return False
    if algorithm != ALGORITHM:
        return False
    return hmac.compare_digest(_pbkdf2(password, salt), expected)


# Checked when the email is unknown, so a wrong email takes as long as a wrong password
# and response times don't reveal which emails have accounts.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def verify_dummy(password: str) -> None:
    verify_password(password, _DUMMY_HASH)


# --- Password rules ------------------------------------------------------------------------

def password_problems(password: str, email: str = "", first_name: str = "", last_name: str = "") -> list[str]:
    """Return what's wrong with a new password (empty list = acceptable)."""
    problems = []
    if len(password) < PASSWORD_MIN:
        problems.append(f"Use at least {PASSWORD_MIN} characters.")
    if len(password) > PASSWORD_MAX:
        problems.append(f"Use at most {PASSWORD_MAX} characters.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        problems.append("Include at least one letter and one number.")
    lower = password.lower()
    if lower in COMMON_PASSWORDS:
        problems.append("That password is too common. Pick something only you would use.")
    personal = [email.split("@")[0], first_name, last_name]
    if any(p and len(p) >= 3 and p.lower() in lower for p in personal):
        problems.append("Don't include your name or email in your password.")
    return problems


# --- Login rate limiting -------------------------------------------------------------------

_failures: dict[str, deque[float]] = defaultdict(deque)


def _recent(key: str) -> deque[float]:
    q = _failures[key]
    cutoff = time.monotonic() - LOGIN_WINDOW_SECONDS
    while q and q[0] < cutoff:
        q.popleft()
    return q


def too_many_failures(key: str) -> bool:
    return len(_recent(key)) >= LOGIN_MAX_FAILURES


def record_failure(key: str) -> None:
    _recent(key).append(time.monotonic())


def clear_failures(key: str) -> None:
    _failures.pop(key, None)


# --- Sessions ------------------------------------------------------------------------------
# The browser keeps a random token in an HttpOnly cookie. The database stores only the token's
# SHA-256, so a leaked database can't be used to log in as anyone.

def ensure_sessions_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )"""
    )


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utc(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def create_session(conn: sqlite3.Connection, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (_token_hash(token), user_id, _utc(now), _utc(now + timedelta(days=SESSION_DAYS))),
    )
    conn.execute("DELETE FROM sessions WHERE expires_at < ?", (_utc(now),))
    return token


def session_user_id(conn: sqlite3.Connection, token: str | None) -> int | None:
    if not token:
        return None
    row = conn.execute(
        "SELECT user_id FROM sessions WHERE token_hash = ? AND expires_at > ?",
        (_token_hash(token), _utc(datetime.now(timezone.utc))),
    ).fetchone()
    return row[0] if row else None


def delete_session(conn: sqlite3.Connection, token: str | None) -> None:
    if token:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))
