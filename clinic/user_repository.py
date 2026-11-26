import sqlite3

from clinic.db import ensure_column
from clinic.user import APPROVED, User

COLUMNS = "id, username, password_hash, role, full_name, doctor_id, status"


class UserRepository:
    """Repository for login accounts. Shares the database connection with the other repositories."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                role TEXT,
                full_name TEXT,
                doctor_id INTEGER
            )
        """)
        ensure_column(conn, "users", "status", f"TEXT DEFAULT '{APPROVED}'")
        conn.commit()

    def add(self, user: User) -> User:
        cur = self.conn.execute(
            "INSERT INTO users (username, password_hash, role, full_name, doctor_id, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                user.username,
                user.password_hash,
                user.role,
                user.full_name,
                user.doctor_id,
                user.status,
            ),
        )
        self.conn.commit()
        user.id = cur.lastrowid
        return user

    def get(self, user_id: int) -> User | None:
        row = self.conn.execute(f"SELECT {COLUMNS} FROM users WHERE id = ?", (user_id,)).fetchone()
        return User(*row) if row else None

    def get_by_username(self, username: str) -> User | None:
        row = self.conn.execute(
            f"SELECT {COLUMNS} FROM users WHERE username = ?", (username,)
        ).fetchone()
        return User(*row) if row else None

    def list_by_status(self, status: str) -> list[User]:
        rows = self.conn.execute(
            f"SELECT {COLUMNS} FROM users WHERE status = ? ORDER BY id", (status,)
        ).fetchall()
        return [User(*row) for row in rows]

    def set_status(self, user_id: int, status: str) -> None:
        self.conn.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
        self.conn.commit()
