from dataclasses import dataclass

PATIENT = "patient"
DOCTOR = "doctor"
ADMIN = "admin"
ROLES = (PATIENT, DOCTOR, ADMIN)

PENDING = "pending"
APPROVED = "approved"
REJECTED = "rejected"


@dataclass
class User:
    """A login account. Only the password hash is stored, never the password itself."""

    id: int | None
    username: str
    password_hash: str
    role: str
    full_name: str
    doctor_id: int | None = None  # kept for older data; doctors are linked by Doctor.user_id
    status: str = APPROVED  # pending until an admin approves doctor and admin requests
