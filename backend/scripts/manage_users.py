# manage_users.py
# Direct, no-email way to create or recover dashboard accounts. Useful when
# SMTP isn't set up, or you just want to set/reset a password by hand.
#
# Usage (run from backend/, with the lenzit conda env active):
#   python scripts/manage_users.py create <username> <email> <password> [--role admin]
#   python scripts/manage_users.py reset-password <username> <new_password>
#   python scripts/manage_users.py list
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from app.core.database import Base, engine, SessionLocal
from app.core.migrations import run_lightweight_migrations
from app.core import security
from app.core.permissions import ROLES
from app.models.user import User
from app.models import agent, group, member, order, logs, settings, user as _user, audit_log  # noqa: registers all tables
from app.services import audit

Base.metadata.create_all(bind=engine)
run_lightweight_migrations(engine)


def create_user(username: str, email: str, password: str, role: str = "admin"):
    username = username.strip().lower()
    email = email.strip().lower()
    if role not in ROLES:
        print(f"Role must be one of: {', '.join(ROLES)}")
        return
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        return

    db = SessionLocal()
    try:
        existing = db.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing:
            print(f"A user with that username or email already exists (id={existing.id}).")
            return
        new_user = User(
            username=username,
            email=email,
            password_hash=security.hash_password(password),
            role=role,
        )
        db.add(new_user)
        db.commit()
        audit.log_action(db, "cli", "user.create", f"user:{username}", f"role={role}")
        print(f"Created user '{username}' <{email}>, role={role}. You can log in now.")
    finally:
        db.close()


def reset_password(username: str, new_password: str):
    username = username.strip().lower()
    if len(new_password) < 8:
        print("Password must be at least 8 characters.")
        return

    db = SessionLocal()
    try:
        target = db.query(User).filter(User.username == username).first()
        if not target:
            print(f"No user named '{username}'.")
            return
        target.password_hash = security.hash_password(new_password)
        target.token_version += 1  # logs out any existing sessions for this user
        target.failed_attempts = 0
        target.locked_until = None
        db.commit()
        audit.log_action(db, "cli", "user.password_reset", f"user:{username}")
        print(f"Password updated for '{username}'. Any existing logged-in sessions were invalidated.")
    finally:
        db.close()


def list_users():
    db = SessionLocal()
    try:
        all_users = db.query(User).all()
        if not all_users:
            print("No users yet.")
            return
        for u in all_users:
            status = "active" if u.is_active else "disabled"
            locked = " (LOCKED)" if u.locked_until else ""
            print(f"id={u.id}  username={u.username}  email={u.email}  role={u.role}  {status}{locked}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="Create a new dashboard user directly")
    p_create.add_argument("username")
    p_create.add_argument("email")
    p_create.add_argument("password")
    p_create.add_argument("--role", default="admin")

    p_reset = sub.add_parser("reset-password", help="Set a new password for an existing user")
    p_reset.add_argument("username")
    p_reset.add_argument("new_password")

    sub.add_parser("list", help="List all dashboard users")

    args = parser.parse_args()
    if args.command == "create":
        create_user(args.username, args.email, args.password, args.role)
    elif args.command == "reset-password":
        reset_password(args.username, args.new_password)
    elif args.command == "list":
        list_users()


if __name__ == "__main__":
    main()
