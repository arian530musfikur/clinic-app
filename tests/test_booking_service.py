from unittest.mock import Mock

import pytest

from clinic.appointment import AppointmentFactory
from clinic.booking_service import BookingService
from clinic.repository import AppointmentRepository


def test_booking_saves_and_notifies():
    repo = Mock()
    repo.is_slot_taken.return_value = False
    repo.add.side_effect = lambda a: (setattr(a, "id", 1), a)[1]
    notifier = Mock()

    saved = BookingService(repo, notifier).book(
        AppointmentFactory.create("Rahim", "Dr. Karim", "10:00")
    )

    assert saved.id == 1
    notifier.send.assert_called_once()


def test_double_booking_is_rejected():
    repo = Mock()
    repo.is_slot_taken.return_value = True
    service = BookingService(repo, Mock())

    with pytest.raises(ValueError):
        service.book(AppointmentFactory.create("Rahim", "Dr. Karim", "10:00"))
    repo.add.assert_not_called()


@pytest.mark.parametrize("blank_name", ["", " ", "\t"])
def test_factory_rejects_blank_patient(blank_name):
    with pytest.raises(ValueError):
        AppointmentFactory.create(blank_name, "Dr. Karim", "10:00")


def test_repository_persists_and_detects_taken_slot():
    repo = AppointmentRepository(":memory:")
    repo.add(AppointmentFactory.create("Rahim", "Dr. Karim", "10:00"))
    assert repo.is_slot_taken("Dr. Karim", "10:00")
    assert not repo.is_slot_taken("Dr. Karim", "11:00")


def test_patient_can_cancel_own_booking_and_slot_is_freed():
    repo = AppointmentRepository(":memory:")
    service = BookingService(repo, Mock())
    appt = service.book(AppointmentFactory.create("Rahim", "Dr. Karim", "10:00", patient_id=1))
    service.cancel(appt.id, patient_id=1)
    assert not repo.is_slot_taken("Dr. Karim", "10:00")


def test_patient_cannot_cancel_another_patients_booking():
    repo = AppointmentRepository(":memory:")
    service = BookingService(repo, Mock())
    appt = service.book(AppointmentFactory.create("Rahim", "Dr. Karim", "10:00", patient_id=1))
    with pytest.raises(ValueError, match="not found"):
        service.cancel(appt.id, patient_id=2)
    assert repo.is_slot_taken("Dr. Karim", "10:00")


def test_cancel_unknown_appointment_with_mock_repo():
    repo = Mock()
    repo.get.return_value = None
    with pytest.raises(ValueError):
        BookingService(repo, Mock()).cancel(99, patient_id=1)
    repo.delete.assert_not_called()
