# app/services/backup_service.py
import os
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger("worker")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BACKEND_DIR, "bot_database.db")
BACKUP_DIR = os.path.join(BACKEND_DIR, "backups")
RETENTION_COUNT = 14  # keep the last 14 daily backups


def backup_database():
    """Uses SQLite's online backup API (safe to run against a live, actively
    written-to database — a plain file copy could grab a half-written page
    and produce a corrupt backup) to snapshot bot_database.db, then prunes
    backups beyond RETENTION_COUNT."""
    if not os.path.exists(DB_PATH):
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dest_path = os.path.join(BACKUP_DIR, f"bot_database_{stamp}.db")

    source = sqlite3.connect(DB_PATH)
    dest = sqlite3.connect(dest_path)
    try:
        source.backup(dest)
        logger.info(f"BACKUP: wrote {dest_path}")
    finally:
        dest.close()
        source.close()

    _prune_old_backups()


def _prune_old_backups():
    backups = sorted(
        (f for f in os.listdir(BACKUP_DIR) if f.startswith("bot_database_") and f.endswith(".db")),
        reverse=True,
    )
    for old in backups[RETENTION_COUNT:]:
        try:
            os.remove(os.path.join(BACKUP_DIR, old))
        except OSError:
            pass
