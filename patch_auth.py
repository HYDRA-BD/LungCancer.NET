"""patch_auth.py — add email/role validation to create_user()."""
from pathlib import Path

AUTH = Path(__file__).parent / "auth.py"
text = AUTH.read_text(encoding="utf-8")

OLD = '''def create_user(name: str, email: str, password: str, role: str = "clinician") -> int:
    email = email.strip().lower()
    init_db()'''

NEW = '''def create_user(name: str, email: str, password: str, role: str = "clinician") -> int:
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        raise ValueError(f"Invalid email: {email!r}")
    if role not in ("clinician", "auditor"):
        raise ValueError(f"Invalid role: {role!r} (must be lowercase 'clinician' or 'auditor')")
    init_db()'''

if OLD in text:
    AUTH.write_text(text.replace(OLD, NEW), encoding="utf-8")
    print("[OK] auth.py patched — create_user now validates email + role")
elif NEW in text:
    print("[SKIP] auth.py already patched")
else:
    print("[ERROR] Could not find create_user function in auth.py")
    print("Open auth.py in your editor and look at the create_user function")