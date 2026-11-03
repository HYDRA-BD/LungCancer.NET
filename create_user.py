"""
create_user.py — Administrative CLI Tool to Provision LungCancer.NET Accounts.

Usage:
  python create_user.py --username drsmith --name "Dr. Jane Smith" --role clinician
  python create_user.py --username auditor1 --name "Alex Auditor" --role auditor --password "SecurePass123!"
"""
from __future__ import annotations

import argparse
import getpass
import sys
from auth import register_user, get_user_count


def main():
    parser = argparse.ArgumentParser(description="Create a secure user account for LungCancer.NET")
    parser.add_argument("--username", "-u", required=False, help="Username or clinical email (min 3 chars)")
    parser.add_argument("--name", "-n", required=False, help="Full clinical name (e.g. 'Dr. Sarah Lin, MD')")
    parser.add_argument("--role", "-r", choices=["clinician", "auditor", "Clinician", "Auditor"], default="Clinician", help="Role: clinician or auditor")
    parser.add_argument("--email", "-e", required=False, help="Optional contact email")
    parser.add_argument("--password", "-p", required=False, help="Password (min 8 chars). If omitted, prompt securely.")

    args = parser.parse_args()

    print("=" * 60)
    print("LungCancer.NET -- User Account Provisioning Tool")
    print("=" * 60)

    username = args.username
    if not username:
        username = input("Enter username or clinical email: ").strip()

    name = args.name
    if not name:
        name = input("Enter full clinical name (e.g. Dr. Jane Doe): ").strip()

    role = args.role.capitalize()

    password = args.password
    if not password:
        password = getpass.getpass("Enter password (min 8 characters): ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("\n❌ Error: Passwords do not match. Aborting.")
            sys.exit(1)

    ok, msg = register_user(
        name=name,
        username_or_email=username,
        password=password,
        role=role,
        email=args.email,
    )

    if ok:
        print(f"\n[OK] {msg}")
        print(f"Total registered accounts in system: {get_user_count()}")
        print("You can now launch the dashboard with: streamlit run app.py")
    else:
        print(f"\n[ERROR] Failed to create user: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
