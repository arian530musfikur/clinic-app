import pytest

from clinic.doctor_repository import DoctorRepository
from clinic.user_repository import UserRepository
from tests.helpers import book, login, logout, register


def test_homepage_lists_doctors(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Dr. Karim" in response.data


@pytest.mark.parametrize(
    ("query", "expected_name"),
    [
        ("Cardiology", b"Dr. Karim"),
        ("Pediatrics", b"Dr. Nusrat Jahan"),
        ("dermatology", b"Dr. Ayesha Rahman"),  # lower case still matches
    ],
)
def test_search_finds_the_right_doctor(client, query, expected_name):
    response = client.get("/", query_string={"q": query})
    assert response.data.count(b'<article class="card">') == 1
    assert expected_name in response.data


def test_search_with_no_match_shows_message(client):
    response = client.get("/", query_string={"q": "zzz-no-such-doctor"})
    assert b"No doctors match" in response.data


def test_booking_requires_login(client, repo):
    response = book(client)
    assert response.status_code == 302
    assert not repo.is_slot_taken("Dr. Karim", "10:00")


def test_patient_can_register_and_is_logged_in(client):
    response = register(client)
    assert b"Your account is ready" in response.data
    assert b"Rahim Uddin" in response.data


def test_patient_booking_is_saved_and_linked_to_account(client, repo):
    register(client)
    book(client)
    assert repo.is_slot_taken("Dr. Karim", "10:00")
    patient_id = UserRepository(repo.conn).get_by_username("rahim").id
    assert len(repo.list_by_patient_id(patient_id)) == 1


def test_double_booking_shows_error_on_page(client):
    register(client)
    book(client)
    response = book(client, follow=True)
    assert b"already booked" in response.data


def test_unknown_doctor_is_rejected(client, repo):
    register(client)
    response = book(client, doctor="Dr. Nobody", follow=True)
    assert b"Choose a doctor from the list" in response.data
    assert not repo.is_slot_taken("Dr. Nobody", "10:00")


def test_my_appointments_shows_own_booking(client):
    register(client)
    book(client, doctor="Dr. Ayesha Rahman", time="12:00")
    response = client.get("/my-appointments")
    assert b"Dr. Ayesha Rahman" in response.data
    assert b"12:00" in response.data


def test_wrong_password_is_rejected(client):
    register(client)
    logout(client)
    response = login(client, "rahim", "wrong-password")
    assert b"Invalid username or password" in response.data


def test_doctor_sees_only_own_patients(client):
    register(client, username="rahim", full_name="Rahim Uddin")
    book(client, doctor="Dr. Karim", time="10:00")
    logout(client)
    register(client, username="sara", full_name="Sara Begum")
    book(client, doctor="Dr. Ayesha Rahman", time="12:00")
    logout(client)

    login(client, "karim", "doctor123")
    response = client.get("/my-patients")
    assert b"Rahim Uddin" in response.data
    assert b"Sara Begum" not in response.data


def test_patient_cannot_open_doctor_page(client):
    register(client)
    assert client.get("/my-patients").status_code == 403


def test_doctor_cannot_book_as_patient(client):
    login(client, "karim", "doctor123")
    assert book(client).status_code == 403


def test_anonymous_user_is_sent_to_login_for_doctor_page(client):
    response = client.get("/my-patients")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_logout_ends_the_session(client):
    register(client)
    logout(client)
    assert client.get("/my-appointments").status_code == 302


def test_seeded_doctor_accounts_exist(client, repo):  # client starts the app, which seeds data
    assert DoctorRepository(repo.conn).get_by_name("Dr. Karim") is not None


def test_login_as_patient_tab_rejects_doctor_account(client):
    response = client.post(
        "/login",
        data={"username": "karim", "password": "doctor123", "role": "patient"},
        follow_redirects=True,
    )
    assert b"does not have the patient role" in response.data


def test_patient_can_cancel_own_booking(client, repo):
    register(client)
    book(client)
    appt_id = repo.list_all()[0].id
    response = client.post(f"/appointments/{appt_id}/cancel", follow_redirects=True)
    assert b"Appointment cancelled" in response.data
    assert not repo.is_slot_taken("Dr. Karim", "10:00")


def test_patient_cannot_cancel_another_patients_booking(client, repo):
    register(client, username="rahim", full_name="Rahim Uddin")
    book(client)
    appt_id = repo.list_all()[0].id
    logout(client)
    register(client, username="sara", full_name="Sara Begum")
    response = client.post(f"/appointments/{appt_id}/cancel", follow_redirects=True)
    assert b"Appointment not found" in response.data
    assert repo.is_slot_taken("Dr. Karim", "10:00")


def test_cancel_requires_login(client):
    assert client.post("/appointments/1/cancel").status_code == 302
