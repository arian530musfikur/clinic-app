import sqlite3
from dataclasses import dataclass

from clinic.db import ensure_column
from clinic.user import APPROVED

SAMPLE_DOCTORS = [
    ("Dr. Karim", "Cardiology", "Central Clinic", "09:00,10:00,11:00"),
    ("Dr. Ayesha Rahman", "Dermatology", "Riverside Hospital", "10:00,12:00,14:00"),
    ("Dr. Imran Hossain", "General Medicine", "Central Clinic", "09:00,13:00,15:00"),
    ("Dr. Nusrat Jahan", "Pediatrics", "Riverside Hospital", "11:00,14:00,16:00"),
]


@dataclass
class Doctor:
    id: int | None
    name: str
    specialty: str
    hospital: str  # the clinic or hospital where the doctor checks patients
    times: str  # checkup times, comma-separated, for example "09:00,10:00"
    status: str = APPROVED  # pending until an admin approves the profile
    user_id: int | None = None  # the doctor's login account

    @property
    def time_list(self) -> list[str]:
        return [t.strip() for t in self.times.split(",") if t.strip()]


class DoctorRepository:
    """Repository for doctor profiles. Shares the database connection with appointments."""

    COLUMNS = "id, name, specialty, hospital, times, status, user_id"

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        conn.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                specialty TEXT,
                hospital TEXT,
                times TEXT
            )
        """)
        ensure_column(conn, "doctors", "status", f"TEXT DEFAULT '{APPROVED}'")
        ensure_column(conn, "doctors", "user_id", "INTEGER")
        conn.commit()

    def add(self, doc: Doctor) -> Doctor:
        cur = self.conn.execute(
            "INSERT INTO doctors (name, specialty, hospital, times, status, user_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (doc.name, doc.specialty, doc.hospital, doc.times, doc.status, doc.user_id),
        )
        self.conn.commit()
        doc.id = cur.lastrowid
        return doc

    def _many(self, sql: str, params: tuple = ()) -> list[Doctor]:
        rows = self.conn.execute(f"SELECT {self.COLUMNS} FROM doctors {sql}", params).fetchall()
        return [Doctor(*row) for row in rows]

    def _one(self, sql: str, params: tuple) -> Doctor | None:
        rows = self._many(sql, params)
        return rows[0] if rows else None

    def list_all(self) -> list[Doctor]:
        return self._many("ORDER BY name")

    def list_approved(self) -> list[Doctor]:
        return self._many("WHERE status = ? ORDER BY name", (APPROVED,))

    def get(self, doctor_id: int) -> Doctor | None:
        return self._one("WHERE id = ?", (doctor_id,))

    def get_by_name(self, name: str) -> Doctor | None:
        return self._one("WHERE name = ?", (name,))

    def get_by_user_id(self, user_id: int) -> Doctor | None:
        return self._one("WHERE user_id = ?", (user_id,))

    def search(self, term: str) -> list[Doctor]:
        """Approved doctors whose name or specialty contains the term."""
        term = term.strip()
        if not term:
            return self.list_approved()
        # Escape LIKE wildcards so a search for "%" or "_" matches literally.
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{escaped}%"
        return self._many(
            "WHERE status = ? AND (name LIKE ? ESCAPE '\\' OR specialty LIKE ? ESCAPE '\\') "
            "ORDER BY name",
            (APPROVED, like, like),
        )

    def set_status(self, doctor_id: int, status: str) -> None:
        self.conn.execute("UPDATE doctors SET status = ? WHERE id = ?", (status, doctor_id))
        self.conn.commit()

    def update_profile(self, doctor_id: int, specialty: str, hospital: str, times: str) -> None:
        self.conn.execute(
            "UPDATE doctors SET specialty = ?, hospital = ?, times = ? WHERE id = ?",
            (specialty, hospital, times, doctor_id),
        )
        self.conn.commit()

    def link_user(self, doctor_id: int, user_id: int) -> None:
        self.conn.execute("UPDATE doctors SET user_id = ? WHERE id = ?", (user_id, doctor_id))
        self.conn.commit()

    def seed_if_empty(self) -> None:
        """Add the sample doctors that are missing (for example, in an older database)."""
        for name, specialty, hospital, times in SAMPLE_DOCTORS:
            if self.get_by_name(name) is None:
                self.add(Doctor(None, name, specialty, hospital, times))
