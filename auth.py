"""
auth.py — Cryptographic Authentication & RBAC Storage for LungCancer.NET.

Key Architecture:
  • Local secure SQLite database (artifacts/users.db).
  • Zero hardcoded credentials in source code, comments, or runtime memory.
  • PBKDF2-HMAC-SHA256 password hashing with 250,000 iterations and 32-byte cryptographically secure random salt.
  • Constant-time verification (hmac.compare_digest) to prevent timing side-channel attacks.
  • Role-Based Access Control (RBAC): 'Clinician' (Full Access) vs 'Auditor' (Read-Only).
  • Brute-force rate limiting: 5 failed attempts locks user out for 60 seconds.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DB_DIR = Path(__file__).parent / "artifacts"
DB_PATH = DB_DIR / "users.db"

PBKDF2_ITERATIONS = 250_000
SALT_BYTES = 32
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 60

# In-memory rate limiting tracking
_FAILED_ATTEMPTS: Dict[str, List[float]] = {}


def _get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection to users.db, initializing tables if needed."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                salt_hex TEXT NOT NULL,
                hash_hex TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    return conn


def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with 250,000 iterations.
    Returns (salt_hex, hash_hex).
    """
    if salt is None:
        salt = os.urandom(SALT_BYTES)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return salt.hex(), derived.hex()


def verify_password(plain_password: str, salt_hex: str, expected_hash_hex: str) -> bool:
    """Constant-time verification of password against salt and expected hash."""
    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hash_hex)
        actual = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def is_rate_limited(identifier: str) -> bool:
    """Checks if an identifier is temporarily locked out."""
    now = time.time()
    attempts = _FAILED_ATTEMPTS.get(identifier, [])
    recent = [t for t in attempts if now - t < LOCKOUT_SECONDS]
    _FAILED_ATTEMPTS[identifier] = recent
    return len(recent) >= MAX_FAILED_ATTEMPTS


def record_failed_attempt(identifier: str) -> None:
    now = time.time()
    if identifier not in _FAILED_ATTEMPTS:
        _FAILED_ATTEMPTS[identifier] = []
    _FAILED_ATTEMPTS[identifier].append(now)


def clear_failed_attempts(identifier: str) -> None:
    if identifier in _FAILED_ATTEMPTS:
        del _FAILED_ATTEMPTS[identifier]


def get_user_count() -> int:
    """Returns the total number of registered users."""
    try:
        with _get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) as cnt FROM users")
            row = cur.fetchone()
            return int(row["cnt"]) if row else 0
    except Exception:
        return 0


def authenticate_user(username_or_email: str, password: str) -> Tuple[bool, Optional[str], Optional[str], str]:
    """
    Authenticates a user against the SQLite database.
    Returns: (success: bool, role: Optional[str], name: Optional[str], message: str)
    """
    clean_id = username_or_email.strip().lower()
    if not clean_id or not password:
        return False, None, None, "Please provide both username/email and password."

    if is_rate_limited(clean_id):
        return False, None, None, f"Too many failed login attempts. Please wait {LOCKOUT_SECONDS} seconds before trying again."

    try:
        with _get_connection() as conn:
            cur = conn.execute(
                "SELECT username, name, role, salt_hex, hash_hex FROM users WHERE username = ? OR email = ?",
                (clean_id, clean_id),
            )
            user = cur.fetchone()

        if not user:
            record_failed_attempt(clean_id)
            return False, None, None, "Invalid credentials. Please verify your login details."

        if verify_password(password, user["salt_hex"], user["hash_hex"]):
            clear_failed_attempts(clean_id)
            return True, user["role"], user["name"], "Authentication successful."

        record_failed_attempt(clean_id)
        return False, None, None, "Invalid credentials. Please verify your login details."

    except Exception as e:
        return False, None, None, f"Authentication service error: {e}"


def register_user(
    name: str,
    username_or_email: str,
    password: str,
    role: str = "Clinician",
    email: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Registers a new user in the database.
    Returns: (success: bool, message: str)
    """
    clean_name = name.strip()
    clean_user = username_or_email.strip().lower()

    if len(clean_name) < 2:
        return False, "Full name must be at least 2 characters long."

    if len(clean_user) < 3 or len(clean_user) > 64:
        return False, "Username or email must be between 3 and 64 characters."

    # Validate username formatting (alphanumeric, dots, underscores, @)
    if not re.match(r"^[\w\.\@\-\+]+$", clean_user):
        return False, "Username or email contains unsupported special characters."

    if len(password) < 8:
        return False, "Password must be at least 8 characters long for clinical data security."

    normalized_role = "Clinician" if role.strip().capitalize() == "Clinician" else "Auditor"

    salt_hex, hash_hex = hash_password(password)
    now_iso = datetime.now().isoformat()
    clean_email = email.strip().lower() if email else (clean_user if "@" in clean_user else "")

    try:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (username, email, name, role, salt_hex, hash_hex, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (clean_user, clean_email, clean_name, normalized_role, salt_hex, hash_hex, now_iso),
            )
        return True, f"Account '{clean_user}' created successfully with role '{normalized_role}'."

    except sqlite3.IntegrityError:
        return False, f"Username or email '{clean_user}' is already registered."
    except Exception as e:
        return False, f"Registration failed: {e}"
