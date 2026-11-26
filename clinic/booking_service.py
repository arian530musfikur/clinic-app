class BookingService:
    """Business rules. Dependencies are injected, so tests can pass mocks."""

    def __init__(self, repo, notifier):
        self.repo = repo          # AppointmentRepository, or a Mock in tests
        self.notifier = notifier  # any Notifier strategy

    def book(self, appt):
        if self.repo.is_slot_taken(appt.doctor, appt.time):
            raise ValueError("This time slot is already booked for that doctor.")
        saved = self.repo.add(appt)
        self.notifier.send(
            saved.patient,
            f"Appointment confirmed with {saved.doctor} at {saved.time}",
        )
        return saved

    def cancel(self, appt_id: int, patient_id: int):
        """Cancel a booking. Only the patient who made it may cancel it."""
        appt = self.repo.get(appt_id)
        if appt is None or appt.patient_id != patient_id:
            raise ValueError("Appointment not found.")
        self.repo.delete(appt_id)
        self.notifier.send(
            appt.patient,
            f"Appointment with {appt.doctor} at {appt.time} was cancelled",
        )
        return appt
