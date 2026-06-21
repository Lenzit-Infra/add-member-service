# app/core/migrations.py
"""
This project has no Alembic. Base.metadata.create_all() only creates
brand-new tables — it never adds columns to a table that already exists.
This runs a tiny set of idempotent ALTER TABLEs for columns added after the
initial schema, so an existing bot_database.db keeps working without manual
surgery.
"""
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

# (table, column, ddl_type)
NEW_COLUMNS = [
    ("agents", "cooldown_until", "DATETIME"),
]


def run_lightweight_migrations(engine: Engine):
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, column, ddl_type in NEW_COLUMNS:
            if table not in existing_tables:
                continue  # table doesn't exist yet — create_all() will make it with the column already
            existing_columns = {c["name"] for c in inspector.get_columns(table)}
            if column not in existing_columns:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"))
                print(f"MIGRATION: added column {table}.{column}")
