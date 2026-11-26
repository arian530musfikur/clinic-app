import pytest

from clinic.appointment import AppointmentFactory


def test_factory_rejects_empty_appointment_time():
    with pytest.raises(ValueError, match="time"):
        AppointmentFactory.create(
            "Rahim",
            "Dr. Karim",
            "",
        )