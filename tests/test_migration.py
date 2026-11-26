"""An existing clinic.db from an earlier version must still work after the update."""

import sqlite3

from werkzeug.security import generate_password_hash

from app import create_app
from clinic.repository import AppointmentRepository
from tests.helpers import login


def make_old_database(path):
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE appointments (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                   patient TEXT, doctor TEXT, time TEXT);
        CREATE TABLE doctors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
                              specialty TEXT, hospital TEXT, times TEXT);
        CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE,
                            password_hash TEXT, role TEXT, full_name TEXT, doctor_id INTEGER);
    """)
    conn.execute("INSERT INTO doctors (name, specialty, hospital, times) VALUES "
                 "('Dr. Karim', 'Cardiology', 'Central Clinic', '09:00,10:00')")
    conn.execute("INSERT INTO users (username, password_hash, role, full_name, doctor_id) "
                 "VALUES ('karim', ?, 'doctor', 'Dr. Karim', 1)",
                 (generate_password_hash("doctor123"),))
    conn.execute("INSERT INTO appointments (patient, doctor, time) VALUES "
                 "('Rahim', 'Dr. Karim', '10:00')")
    conn.commit()
    conn.close()


def test_old_database_is_upgraded_and_still_works(tmp_path):
    database_file = tmp_path / "clinic.db"
    make_old_database(database_file)

    repo = AppointmentRepository(str(database_file))
    client = create_app(repo).test_client()

    # Old accounts become approved, and the old doctor profile is linked to its login.
    response = login(client, "karim", "doctor123", role="doctor")
    assert b"Welcome back" in response.data
    assert b"Rahim" in client.get("/my-patients").data
    assert b"Dr. Karim" in client.get("/", query_string={"q": "Cardiology"}).data
    # The old booking is still there.
    assert [a.patient for a in repo.list_all()] == ["Rahim"]
