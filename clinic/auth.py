from werkzeug.security import check_password_hash, generate_password_hash

from clinic.user import ADMIN, APPROVED, DOCTOR, PATIENT, PENDING, REJECTED, User

MIN_PASSWORD_LENGTH = 6


class AuthService:
    """Accounts (business rules): sign-up, approval status, and login.

    Passwords are stored as hashes only. Patients are active at once. Doctor and admin
    accounts start as pending and can log in only after an admin approves them.
    """

    def __init__(self, users):
        self.users = users  # UserRepository, or a Mock in tests

    def register(self, role: str, username: str, password: str, full_name: str,
                 doctor_id: int | None = None) -> User:
        self.check_new_account(username, password, full_name)
        status = APPROVED if role == PATIENT else PENDING
        user = User(None, username.strip(), generate_password_hash(password), role,
                    full_name.strip(), doctor_id, status)
        return self.users.add(user)

    def register_patient(self, username: str, password: str, full_name: str) -> User:
        return self.register(PATIENT, username, password, full_name)

    def create_doctor_account(self, username: str, password: str, full_name: str,
                              doctor_id: int | None = None) -> User:
        """Approved doctor login, used by the admin page and the demo setup."""
        self.check_new_account(username, password, full_name)
        user = User(None, username.strip(), generate_password_hash(password), DOCTOR,
                    full_name.strip(), doctor_id, APPROVED)
        return self.users.add(user)

    def create_admin_account(self, username: str, password: str, full_name: str) -> User:
        """Approved admin login, used by the demo setup."""
        self.check_new_account(username, password, full_name)
        user = User(None, username.strip(), generate_password_hash(password), ADMIN,
                    full_name.strip(), None, APPROVED)
        return self.users.add(user)

    def check_new_account(self, username: str, password: str, full_name: str) -> None:
        if not username.strip() or not full_name.strip():
            raise ValueError("Username and full name are required.")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
        if self.users.get_by_username(username.strip()) is not None:
            raise ValueError("That username is already taken.")

    def login(self, username: str, password: str, role: str | None = None) -> User:
        user = self.users.get_by_username(username.strip())
        if user is None or not check_password_hash(user.password_hash, password):
            raise ValueError("Invalid username or password.")
        if role and user.role != role:
            raise ValueError(f"This account does not have the {role} role.")
        if user.status == PENDING:
            raise ValueError("Your account is waiting for admin approval.")
        if user.status == REJECTED:
            raise ValueError("This request was not approved. Contact the clinic admin.")
        return user
