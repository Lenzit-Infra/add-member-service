import os
import sqlite3
import app.services.backup_service as backup_service


def test_backup_creates_a_valid_sqlite_copy(tmp_path, monkeypatch):
    db_path = tmp_path / "bot_database.db"
    backup_dir = tmp_path / "backups"

    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
    conn.execute("INSERT INTO t (val) VALUES ('hello')")
    conn.commit()
    conn.close()

    monkeypatch.setattr(backup_service, "DB_PATH", str(db_path))
    monkeypatch.setattr(backup_service, "BACKUP_DIR", str(backup_dir))

    backup_service.backup_database()

    files = os.listdir(backup_dir)
    assert len(files) == 1

    copy_conn = sqlite3.connect(backup_dir / files[0])
    rows = copy_conn.execute("SELECT val FROM t").fetchall()
    copy_conn.close()
    assert rows == [("hello",)]


def test_backup_prunes_beyond_retention_count(tmp_path, monkeypatch):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    monkeypatch.setattr(backup_service, "BACKUP_DIR", str(backup_dir))
    monkeypatch.setattr(backup_service, "RETENTION_COUNT", 3)

    for i in range(5):
        (backup_dir / f"bot_database_2026010{i}_000000.db").write_text("x")

    backup_service._prune_old_backups()
    assert len(os.listdir(backup_dir)) == 3


def test_backup_does_nothing_if_db_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(backup_service, "DB_PATH", str(tmp_path / "nope.db"))
    monkeypatch.setattr(backup_service, "BACKUP_DIR", str(tmp_path / "backups"))
    backup_service.backup_database()  # should not raise
    assert not (tmp_path / "backups").exists()
