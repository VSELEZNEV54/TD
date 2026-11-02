"""Local setup and consistent SQLite backup; no external delivery."""

import argparse
import os
import secrets
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def init_env():
    target = ROOT / ".env"
    token = secrets.token_urlsafe(40)
    content = "\n".join([
        "# Local configuration. Never commit or put inside site/.",
        "ADMIN_TOKEN=" + token,
        "PUBLIC_ORIGIN=",
        "TRUST_PROXY=false",
        "REGISTER_URL=https://app.teacherdesk.ru/register",
        "LOGIN_URL=https://app.teacherdesk.ru/login",
        "RATE_LIMIT=5", "RATE_WINDOW=600", "",
    ])
    fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        output.write(content)
    print("Created .env. Read ADMIN_TOKEN in that file to enter /admin/.")


def backup(destination):
    # Import only after init-env has had a chance to create the configuration.
    from .app import application
    destination = Path(destination).expanduser().resolve()
    site = application.config["SITE_DIR"]
    if destination == site or site in destination.parents:
        raise ValueError("Backup must be outside public site/")
    if destination.exists():
        raise FileExistsError("Backup destination already exists")
    if destination == application.database:
        raise ValueError("Choose a separate backup file")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(destination), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    source = application.connect()
    target = sqlite3.connect(str(destination))
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    print("SQLite backup created: " + str(destination))


def main():
    parser = argparse.ArgumentParser(description="TeacherDesk setup and backup")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init-env", help="Create .env with a new admin token, never overwrite")
    backup_parser = commands.add_parser("backup", help="Back up the SQLite database safely")
    backup_parser.add_argument("destination")
    args = parser.parse_args()
    try:
        if args.command == "init-env":
            init_env()
        else:
            backup(args.destination)
    except (OSError, ValueError, sqlite3.Error) as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
