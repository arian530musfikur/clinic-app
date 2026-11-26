from dataclasses import dataclass


@dataclass
class Appointment:
    id: int | None
    patient: str
    doctor: str
    time: str
    patient_id: int | None = None


class AppointmentFactory:
    """Factory: creates and validates appointments."""

    @staticmethod
    def create(
        patient: str, doctor: str, time: str, patient_id: int | None = None
    ) -> Appointment:
        if (
            not patient.strip()
            or not doctor.strip()
            or not time.strip()
            or len(patient.strip()) > 100
        ):
            raise ValueError(
                "Patient name and doctor are required; "
                "time is required and patient name must be at most 100 characters."
            )

        return Appointment(
            None,
            patient.strip(),
            doctor.strip(),
            time,
            patient_id,
        )