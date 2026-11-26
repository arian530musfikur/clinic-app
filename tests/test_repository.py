from clinic.appointment import AppointmentFactory
from clinic.repository import AppointmentRepository


def test_list_all_returns_saved_appointments():
    repo = AppointmentRepository(":memory:")
    repo.add(AppointmentFactory.create("Rahim", "Dr. Karim", "10:00"))
    repo.add(AppointmentFactory.create("Sara", "Dr. Karim", "11:00"))
    assert [a.patient for a in repo.list_all()] == ["Rahim", "Sara"]


def test_list_by_doctor_filters_and_sorts_by_time():
    repo = AppointmentRepository(":memory:")
    repo.add(AppointmentFactory.create("Sara", "Dr. Karim", "11:00"))
    repo.add(AppointmentFactory.create("Rahim", "Dr. Karim", "10:00"))
    repo.add(AppointmentFactory.create("Other", "Dr. Ayesha Rahman", "10:00"))
    assert [a.patient for a in repo.list_by_doctor("Dr. Karim")] == ["Rahim", "Sara"]


def test_list_by_patient_id_returns_only_that_patients_bookings():
    repo = AppointmentRepository(":memory:")
    repo.add(AppointmentFactory.create("Rahim", "Dr. Karim", "10:00", patient_id=1))
    repo.add(AppointmentFactory.create("Sara", "Dr. Karim", "11:00", patient_id=2))
    result = repo.list_by_patient_id(1)
    assert [a.time for a in result] == ["10:00"]
