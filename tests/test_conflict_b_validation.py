import pytest

from clinic.appointment import AppointmentFactory


def test_factory_rejects_patient_name_over_100_characters():
    long_name = "R" * 101

    with pytest.raises(ValueError, match="100 characters"):
        AppointmentFactory.create(
            long_name,
            "Dr. Karim",
            "10:00",
        )