import sqlite3


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    """Migration helper: add a column to a table created by an older version of the app."""
    columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
