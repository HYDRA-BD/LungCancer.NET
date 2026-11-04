"""
create_user.py — create a user account from the command line.

This is the ONLY way to create your first account. Credentials are never
stored in code. Run this from your project folder:

    python create_user.py --name "Dr. Your Name" --email you@example.com --role clinician

Password will be prompted interactively.
"""
import argparse
import getpass
import sys

from auth import create_user, get_user_by_email, init_db


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--email", required=True)
    ap.add_argument("--role", default="clinician", choices=["clinician", "auditor"])
    ap.add_argument("--password", help="Password (omit to prompt securely)")
    args = ap.parse_args()

    init_db()
    if get_user_by_email(args.email):
        print(f"[ERROR] Email already registered: {args.email}")
        sys.exit(1)

    password = args.password
    if not password:
        password = getpass.getpass("Password (min 8 chars): ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("[ERROR] Passwords do not match")
            sys.exit(1)

    if len(password) < 8:
        print("[ERROR] Password must be at least 8 characters")
        sys.exit(1)

    user_id = create_user(args.name, args.email, password, args.role)
    print()
    print(f"[OK] User created")
    print(f"     ID:    {user_id}")
    print(f"     Name:  {args.name}")
    print(f"     Email: {args.email}")
    print(f"     Role:  {args.role}")
    print()
    print(f"Log in at: http://localhost:8000/docs or your React frontend")


if __name__ == "__main__":
    main()