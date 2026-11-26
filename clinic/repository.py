import sqlite3

from clinic.appointment import Appointment

COLUMNS = "id, patient, doctor, time, patient_id"


class AppointmentRepository:
    """Repository (structural): hides SQLite details behind simple methods."""

    def __init__(self, path: str = "clinic.db"):
        # check_same_thread=False lets the Flask dev server use the connection from any thread
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient TEXT,
                doctor TEXT,
                time TEXT
            )
        """)
        # Migration: add the patient_id column to databases created before accounts existed.
        columns = [row[1] for row in self.conn.execute("PRAGMA table_info(appointments)")]
        if "patient_id" not in columns:
            self.conn.execute("ALTER TABLE appointments ADD COLUMN patient_id INTEGER")
        self.conn.commit()

    def add(self, appt: Appointment) -> Appointment:
        cur = self.conn.execute(
            "INSERT INTO appointments (patient, doctor, time, patient_id) VALUES (?, ?, ?, ?)",
            (appt.patient, appt.doctor, appt.time, appt.patient_id),
        )
        self.conn.commit()
        appt.id = cur.lastrowid
        return appt

    def is_slot_taken(self, doctor: str, time: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM appointments WHERE doctor = ? AND time = ?",
            (doctor, time),
        ).fetchone()
        return row is not None

    def get(self, appt_id: int) -> Appointment | None:
        row = self.conn.execute(
            f"SELECT {COLUMNS} FROM appointments WHERE id = ?", (appt_id,)
        ).fetchone()
        return Appointment(*row) if row else None

    def delete(self, appt_id: int) -> None:
        self.conn.execute("DELETE FROM appointments WHERE id = ?", (appt_id,))
        self.conn.commit()

    def list_all(self) -> list[Appointment]:
        rows = self.conn.execute(f"SELECT {COLUMNS} FROM appointments ORDER BY id").fetchall()
        return [Appointment(*row) for row in rows]

    def list_by_doctor(self, doctor: str) -> list[Appointment]:
        rows = self.conn.execute(
            f"SELECT {COLUMNS} FROM appointments WHERE doctor = ? ORDER BY time",
            (doctor,),
        ).fetchall()
        return [Appointment(*row) for row in rows]

    def list_by_patient_id(self, patient_id: int) -> list[Appointment]:
        rows = self.conn.execute(
            f"SELECT {COLUMNS} FROM appointments WHERE patient_id = ? ORDER BY time",
            (patient_id,),
        ).fetchall()
        return [Appointment(*row) for row in rows]
