from dataclasses import dataclass


@dataclass
class Appointment:
    id: int | None
    patient: str
    doctor: str
    time: str
    patient_id: int | None = None  # links the booking to the patient's account


class AppointmentFactory:
    """Factory (creational): the single place where appointments are created and validated."""

    @staticmethod
    def create(
        patient: str, doctor: str, time: str, patient_id: int | None = None
    ) -> Appointment:
        if not patient.strip() or not doctor.strip() or not time.strip():
            raise ValueError("Patient name, doctor, and time are required.")
        return Appointment(None, patient.strip(), doctor.strip(), time, patient_id)
