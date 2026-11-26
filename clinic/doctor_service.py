import re

from clinic.doctor_repository import Doctor, DoctorRepository
from clinic.user import ADMIN, APPROVED, DOCTOR, PENDING, REJECTED

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")  # 00:00 to 23:59


class DoctorService:
    """Doctor and admin rules: sign-up requests, profile edits, and approval."""

    def __init__(self, doctors: DoctorRepository, auth):
        self.doctors = doctors
        self.auth = auth

    @staticmethod
    def parse_times(times: str) -> list[str]:
        slots = [t.strip() for t in times.split(",") if t.strip()]
        if not slots:
            raise ValueError("Enter at least one checkup time, such as 09:00,10:00.")
        bad = [t for t in slots if not TIME_PATTERN.match(t)]
        if bad:
            raise ValueError(f"Times must look like 09:00. Check: {', '.join(bad)}")
        return slots

    def _check_profile(self, name: str, specialty: str, hospital: str, times: str) -> list[str]:
        if not name.strip() or not specialty.strip() or not hospital.strip():
            raise ValueError("Name, specialty and clinic are required.")
        if self.doctors.get_by_name(name.strip()) is not None:
            raise ValueError(f"A doctor named {name.strip()} already exists.")
        return self.parse_times(times)

    def request_doctor_signup(self, username: str, password: str, full_name: str,
                              specialty: str, hospital: str, times: str):
        """A doctor creates an account and a profile. The profile waits for admin approval."""
        slots = self._check_profile(full_name, specialty, hospital, times)
        self.auth.check_new_account(username, password, full_name)
        user = self.auth.register(DOCTOR, username, password, full_name)
        doctor = self.doctors.add(Doctor(None, full_name.strip(), specialty.strip(),
                                         hospital.strip(), ",".join(slots), PENDING, user.id))
        return user, doctor

    def add_doctor(self, name: str, specialty: str, hospital: str, times: str,
                   username: str = "", password: str = ""):
        """An admin adds a doctor directly. The profile is approved at once."""
        slots = self._check_profile(name, specialty, hospital, times)
        user_id = None
        if username.strip():
            if len(password) < 6:
                raise ValueError("Password must be at least 6 characters.")
            self.auth.check_new_account(username, password, name)
            user_id = self.auth.create_doctor_account(username, password, name).id
        return self.doctors.add(Doctor(None, name.strip(), specialty.strip(), hospital.strip(),
                                       ",".join(slots), APPROVED, user_id))

    def update_profile(self, doctor_id: int, specialty: str, hospital: str, times: str) -> None:
        if not specialty.strip() or not hospital.strip():
            raise ValueError("Specialty and clinic are required.")
        slots = self.parse_times(times)
        self.doctors.update_profile(doctor_id, specialty.strip(), hospital.strip(), ",".join(slots))

    def decide(self, user_id: int, approve: bool) -> None:
        """Approve or reject a pending doctor or admin request."""
        user = self.auth.users.get(user_id)
        if user is None or user.role not in (DOCTOR, ADMIN):
            raise ValueError("Request not found.")
        if user.status != PENDING:
            raise ValueError("This request has already been decided.")
        status = APPROVED if approve else REJECTED
        self.auth.users.set_status(user_id, status)
        if user.role == DOCTOR:
            doctor = self.doctors.get_by_user_id(user_id)
            if doctor is not None:
                self.doctors.set_status(doctor.id, status)
