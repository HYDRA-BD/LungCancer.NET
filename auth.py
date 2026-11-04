"""
auth.py — secure password hashing, JWT tokens, SQLite user storage.

Password hashing: PBKDF2-HMAC-SHA256, 480,000 iterations (OWASP 2024 recommendation).
No bcrypt dependency — pure stdlib, works reliably on Windows.
Tokens: HS256 JWT, 8-hour expiry.
Storage: SQLite at artifacts/users.db (never committed to git).
"""
import hashlib
import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import jwt

# ── JWT secret: env var, else persistent file ───────────────────────
_SECRET_FILE = Path(__file__).parent / "artifacts" / ".jwt_secret"

def _load_jwt_secret() -> str:
    env = os.environ.get("JWT_SECRET")
    if env:
        return env
    if _SECRET_FILE.exists():
        return _SECRET_FILE.read_text().strip()
    _SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
    secret = secrets.token_hex(32)
    _SECRET_FILE.write_text(secret)
    return secret

JWT_SECRET = _load_jwt_secret()
JWT_ALG = "HS256"
JWT_EXP_HOURS = 8
PBKDF2_ITERATIONS = 480_000
USERS_DB = Path(__file__).parent / "artifacts" / "users.db"


# ── Storage ─────────────────────────────────────────────────────────
def init_db() -> None:
    USERS_DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(USERS_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('clinician', 'auditor')),
                created_at TEXT NOT NULL,
                last_login TEXT
            )
        """)
        conn.commit()


# ── Password hashing ───────────────────────────────────────────────
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iter_str, salt_hex, digest_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(iter_str)
        )
        return secrets.compare_digest(expected, actual)
    except Exception:
        return False


# ── Tokens ──────────────────────────────────────────────────────────
def create_token(user_id: int, email: str, role: str) -> str:
    now = datetime.utcnow()
    return jwt.encode(
        {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "iat": now,
            "exp": now + timedelta(hours=JWT_EXP_HOURS),
        },
        JWT_SECRET,
        algorithm=JWT_ALG,
    )


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except Exception:
        return None


# ── User CRUD ──────────────────────────────────────────────────────
def create_user(name: str, email: str, password: str, role: str = "clinician") -> int:
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        raise ValueError(f"Invalid email: {email!r}")
    if role not in ("clinician", "auditor"):
        raise ValueError(f"Invalid role: {role!r} (must be lowercase 'clinician' or 'auditor')")
    init_db()
    with sqlite3.connect(USERS_DB) as conn:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, role, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (name.strip(), email, hash_password(password), role,
             datetime.utcnow().isoformat()),
        )
        conn.commit()
        return cur.lastrowid


def get_user_by_email(email: str) -> Optional[dict]:
    init_db()
    with sqlite3.connect(USERS_DB) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[dict]:
    init_db()
    with sqlite3.connect(USERS_DB) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def update_last_login(user_id: int) -> None:
    init_db()
    with sqlite3.connect(USERS_DB) as conn:
        conn.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), user_id),
        )
        conn.commit()