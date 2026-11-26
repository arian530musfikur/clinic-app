import pytest
from werkzeug.security import check_password_hash


def test_registered_patient_has_patient_role(auth):
    user = auth.register_patient("rahim", "secret123", "Rahim Uddin")
    assert user.role == "patient"
    assert user.full_name == "Rahim Uddin"


def test_password_is_stored_as_hash_not_plain_text(auth):
    auth.register_patient("rahim", "secret123", "Rahim Uddin")
    stored = auth.users.get_by_username("rahim")
    assert stored.password_hash != "secret123"
    assert check_password_hash(stored.password_hash, "secret123")


def test_duplicate_username_is_rejected(auth):
    auth.register_patient("rahim", "secret123", "Rahim Uddin")
    with pytest.raises(ValueError, match="already taken"):
        auth.register_patient("rahim", "other456", "Someone Else")


@pytest.mark.parametrize("short_password", ["", "1", "12345"])  # parametrize: many cases, one test
def test_short_password_is_rejected(auth, short_password):
    with pytest.raises(ValueError, match="at least 6"):
        auth.register_patient("rahim", short_password, "Rahim Uddin")


@pytest.mark.parametrize(
    ("username", "full_name"),
    [("   ", "Rahim Uddin"), ("rahim", "   "), ("", "Rahim Uddin")],
)
def test_blank_username_or_name_is_rejected(auth, username, full_name):
    with pytest.raises(ValueError, match="required"):
        auth.register_patient(username, "secret123", full_name)


def test_login_with_correct_password_returns_user(auth):
    auth.register_patient("rahim", "secret123", "Rahim Uddin")
    assert auth.login("rahim", "secret123").username == "rahim"


@pytest.mark.parametrize(
    ("username", "password"),
    [("rahim", "wrong-password"), ("nobody", "secret123")],
)
def test_login_failures_use_the_same_message(auth, username, password):
    auth.register_patient("rahim", "secret123", "Rahim Uddin")
    with pytest.raises(ValueError, match="Invalid username or password"):
        auth.login(username, password)


def test_doctor_account_has_doctor_role_and_link(auth):
    user = auth.create_doctor_account("karim", "doctor123", "Dr. Karim", doctor_id=1)
    assert user.role == "doctor"
    assert user.doctor_id == 1


def test_login_with_matching_role_succeeds(auth):
    auth.register_patient("rahim", "secret123", "Rahim Uddin")
    assert auth.login("rahim", "secret123", role="patient").role == "patient"


def test_login_with_wrong_role_is_rejected(auth):
    auth.register_patient("rahim", "secret123", "Rahim Uddin")
    with pytest.raises(ValueError, match="does not have the doctor role"):
        auth.login("rahim", "secret123", role="doctor")
