"""Persistence test using pytest's built-in tmp_path fixture (NFR-01: data survives restart)."""

from unittest.mock import Mock

from clinic.appointment import AppointmentFactory
from clinic.booking_service import BookingService
from clinic.repository import AppointmentRepository


def test_booking_survives_application_restart(tmp_path):
    database_file = tmp_path / "clinic.db"  # a real file, deleted automatically after the test

    first_run = AppointmentRepository(str(database_file))
    BookingService(first_run, Mock()).book(
        AppointmentFactory.create("Rahim", "Dr. Karim", "10:00")
    )
    first_run.conn.close()  # simulate stopping the application

    second_run = AppointmentRepository(str(database_file))
    assert second_run.is_slot_taken("Dr. Karim", "10:00")
