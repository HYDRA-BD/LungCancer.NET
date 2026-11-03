"""
auth.py — Cryptographic Authentication & Role-Based Access Control for LungCancer.NET.

Implements:
  • Secure password hashing and verification using bcrypt (12 rounds)
  • Role-Based Access Control (RBAC): 'Clinician' (Full Access) vs 'Auditor' (Read-Only)
  • Ephemeral in-memory credential store (no patient data ever written to disk)
  • Protection against brute-force login attempts (rate limiting / failure tracking)
"""
from __future__ import annotations

import time
from typing import Dict, Optional, Tuple

import bcrypt

# Pre-configured default credentials for clinical evaluation
# In production, these can be initialized from secure environment variables.
_DEFAULT_USERS = {
    "clinician": {
        "name": "Dr. Sarah Lin, MD (Attending Pulmonologist)",
        # bcrypt hash of 'ClinicianPass2026!'
        "hash": bcrypt.hashpw("ClinicianPass2026!".encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8"),
        "role": "Clinician",
    },
    "auditor": {
        "name": "Alex Mercer (Clinical AI Quality Auditor)",
        # bcrypt hash of 'AuditorPass2026!'
        "hash": bcrypt.hashpw("AuditorPass2026!".encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8"),
        "role": "Auditor",
    },
}

# In-memory user database for the running session (ephemeral)
_USER_STORE: Dict[str, dict] = dict(_DEFAULT_USERS)

# In-memory tracking of failed login attempts for rate limiting
_LOGIN_ATTEMPTS: Dict[str, list] = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 60


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with salt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def is_rate_limited(username: str) -> bool:
    """Check if an account or IP is temporarily locked out due to excessive failed attempts."""
    now = time.time()
    attempts = _LOGIN_ATTEMPTS.get(username, [])
    # Keep only attempts within the lockout window
    recent = [t for t in attempts if now - t < LOCKOUT_DURATION_SECONDS]
    _LOGIN_ATTEMPTS[username] = recent
    return len(recent) >= MAX_FAILED_ATTEMPTS


def record_failed_attempt(username: str) -> None:
    """Record a failed login timestamp."""
    now = time.time()
    if username not in _LOGIN_ATTEMPTS:
        _LOGIN_ATTEMPTS[username] = []
    _LOGIN_ATTEMPTS[username].append(now)


def clear_failed_attempts(username: str) -> None:
    """Clear failed attempts on successful login."""
    if username in _LOGIN_ATTEMPTS:
        del _LOGIN_ATTEMPTS[username]


def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[str], Optional[str], str]:
    """
    Authenticate a user.
    Returns: (success: bool, role: Optional[str], display_name: Optional[str], message: str)
    """
    clean_user = username.strip().lower()
    if not clean_user or not password:
        return False, None, None, "Username and password are required."

    if is_rate_limited(clean_user):
        return False, None, None, f"Too many failed login attempts. Please wait {LOCKOUT_DURATION_SECONDS} seconds."

    user_record = _USER_STORE.get(clean_user)
    if not user_record:
        record_failed_attempt(clean_user)
        return False, None, None, "Invalid username or password."

    if verify_password(password, user_record["hash"]):
        clear_failed_attempts(clean_user)
        return True, user_record["role"], user_record["name"], "Authentication successful."

    record_failed_attempt(clean_user)
    return False, None, None, "Invalid username or password."


def register_user(username: str, password: str, display_name: str, role: str) -> Tuple[bool, str]:
    """
    Register a new user in the session store.
    Returns: (success: bool, message: str)
    """
    clean_user = username.strip().lower()
    if len(clean_user) < 3 or len(clean_user) > 32:
        return False, "Username must be between 3 and 32 characters."

    if not clean_user.replace("_", "").isalnum():
        return False, "Username can only contain alphanumeric characters and underscores."

    if clean_user in _USER_STORE:
        return False, "Username is already registered."

    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    if role not in ["Clinician", "Auditor"]:
        return False, "Role must be either 'Clinician' or 'Auditor'."

    clean_name = display_name.strip()[:60] if display_name else f"User {clean_user}"

    _USER_STORE[clean_user] = {
        "name": clean_name,
        "hash": hash_password(password),
        "role": role,
    }
    return True, f"Account '{clean_user}' created successfully with role '{role}'."
