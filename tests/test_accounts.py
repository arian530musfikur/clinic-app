"""Sign-up for patient, doctor, and admin; approval workflow; doctor profile edits."""

import pytest

from clinic.user import APPROVED, DOCTOR, PATIENT, PENDING, REJECTED
from clinic.user_repository import UserRepository
from tests.helpers import book, login, logout, register


def doctor_form(**overrides):
    form = {
        "full_name": "Dr. Sadia Noor",
        "username": "sadia",
        "password": "doctor123",
        "specialty": "Neurology",
        "hospital": "Lakeside Clinic",
        "times": "09:00,11:00",
    }
    form.update(overrides)
    return form


def admin_login(client):
    return login(client, "admin", "admin123", role="admin")


def sign_up_doctor(client, **overrides):
    return client.post("/register/doctor", data=doctor_form(**overrides), follow_redirects=True)


def test_register_page_offers_three_account_types(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"/register/patient" in response.data
    assert b"/register/doctor" in response.data
    assert b"/register/admin" in response.data


def test_patient_sign_up_is_active_immediately(client, repo):
    register(client)
    user = UserRepository(repo.conn).get_by_username("rahim")
    assert user.role == PATIENT
    assert user.status == APPROVED


def test_doctor_sign_up_creates_a_pending_profile(client, repo, doctors):
    response = sign_up_doctor(client)
    assert b"Doctor request sent" in response.data
    doc = doctors.get_by_name("Dr. Sadia Noor")
    assert doc.status == PENDING
    assert doc.specialty == "Neurology"
    assert doc.time_list == ["09:00", "11:00"]
    assert UserRepository(repo.conn).get_by_username("sadia").role == DOCTOR


def test_pending_doctor_cannot_log_in(client):
    sign_up_doctor(client)
    response = login(client, "sadia", "doctor123", role="doctor")
    assert b"waiting for admin approval" in response.data


def test_pending_doctor_is_not_in_search(client):
    sign_up_doctor(client)
    response = client.get("/", query_string={"q": "Neurology"})
    assert b"Dr. Sadia Noor" not in response.data


def test_full_doctor_approval_flow(repo, client, doctors):
    sign_up_doctor(client)
    logout(client)
    admin_login(client)
    doctor = doctors.get_by_name("Dr. Sadia Noor")
    user_id = doctor.user_id
    client.post(f"/admin/requests/{user_id}/approve", follow_redirects=True)
    logout(client)

    response = login(client, "sadia", "doctor123", role="doctor")
    assert b"Welcome back" in response.data
    assert doctors.get_by_name("Dr. Sadia Noor").status == APPROVED
    assert b"Dr. Sadia Noor" in client.get("/", query_string={"q": "Neurology"}).data


def test_admin_rejects_doctor_request(client, doctors):
    sign_up_doctor(client)
    logout(client)
    admin_login(client)
    user_id = doctors.get_by_name("Dr. Sadia Noor").user_id
    client.post(f"/admin/requests/{user_id}/reject", follow_redirects=True)
    logout(client)
    response = login(client, "sadia", "doctor123", role="doctor")
    assert b"was not approved" in response.data
    assert doctors.get_by_name("Dr. Sadia Noor").status == REJECTED


def test_pending_doctor_cannot_be_booked(client):
    sign_up_doctor(client)
    logout(client)
    register(client, username="rahim", full_name="Rahim Uddin")
    response = book(client, doctor="Dr. Sadia Noor", time="09:00", follow=True)
    assert b"Choose a doctor from the list" in response.data


def test_doctor_sign_up_needs_clinic_and_valid_times(client, doctors):
    response = sign_up_doctor(client, hospital="", times="9am")
    assert b"required" in response.data or b"Times must look like" in response.data
    assert doctors.get_by_name("Dr. Sadia Noor") is None


def test_admin_sign_up_waits_for_approval(client):
    response = client.post(
        "/register/admin",
        data={"full_name": "New Admin", "username": "newadmin", "password": "secret123"},
        follow_redirects=True,
    )
    assert b"Admin request sent" in response.data
    response = login(client, "newadmin", "secret123", role="admin")
    assert b"waiting for admin approval" in response.data


def test_approved_admin_can_log_in_and_open_admin_page(client, repo, doctors):
    client.post(
        "/register/admin",
        data={"full_name": "New Admin", "username": "newadmin", "password": "secret123"},
    )
    logout(client)
    admin_login(client)
    new_admin = UserRepository(repo.conn).get_by_username("newadmin")
    client.post(f"/admin/requests/{new_admin.id}/approve")
    logout(client)
    login(client, "newadmin", "secret123", role="admin")
    assert client.get("/admin").status_code == 200


def test_only_admin_can_decide_requests(client, doctors):
    sign_up_doctor(client)
    logout(client)
    register(client, username="rahim", full_name="Rahim Uddin")
    user_id = doctors.get_by_name("Dr. Sadia Noor").user_id
    assert client.post(f"/admin/requests/{user_id}/approve").status_code == 403


def test_approved_doctor_can_edit_profile_and_patients_see_it(client, doctors):
    sign_up_doctor(client)
    logout(client)
    admin_login(client)
    client.post(f"/admin/requests/{doctors.get_by_name('Dr. Sadia Noor').user_id}/approve")
    logout(client)
    login(client, "sadia", "doctor123", role="doctor")

    response = client.post(
        "/doctor/profile",
        data={"specialty": "Neurology", "hospital": "Riverside Clinic", "times": "10:00,12:00"},
        follow_redirects=True,
    )
    assert b"Profile saved" in response.data
    updated = doctors.get_by_name("Dr. Sadia Noor")
    assert updated.hospital == "Riverside Clinic"
    assert updated.time_list == ["10:00", "12:00"]


@pytest.mark.parametrize("times", ["", "99:00", "ten"])
def test_doctor_profile_rejects_bad_times(client, doctors, times):
    sign_up_doctor(client)
    logout(client)
    admin_login(client)
    client.post(f"/admin/requests/{doctors.get_by_name('Dr. Sadia Noor').user_id}/approve")
    logout(client)
    login(client, "sadia", "doctor123", role="doctor")
    before = doctors.get_by_name("Dr. Sadia Noor").times
    client.post("/doctor/profile", data={"specialty": "N", "hospital": "H", "times": times})
    assert doctors.get_by_name("Dr. Sadia Noor").times == before


def test_patient_cannot_open_doctor_profile(client):
    register(client)
    assert client.get("/doctor/profile").status_code == 403


def test_admin_can_edit_any_doctor_profile(client, doctors):
    admin_login(client)
    karim = doctors.get_by_name("Dr. Karim")
    client.post(
        f"/admin/doctors/{karim.id}/edit",
        data={"specialty": "Cardiology", "hospital": "New Wing", "times": "13:00"},
        follow_redirects=True,
    )
    assert doctors.get(karim.id).hospital == "New Wing"
    assert doctors.get(karim.id).time_list == ["13:00"]


def test_admin_dashboard_shows_pending_count(client):
    sign_up_doctor(client)
    logout(client)
    admin_login(client)
    response = client.get("/")
    assert b"Pending requests" in response.data


def test_admin_decision_twice_is_rejected(client, doctors):
    sign_up_doctor(client)
    logout(client)
    admin_login(client)
    user_id = doctors.get_by_name("Dr. Sadia Noor").user_id
    client.post(f"/admin/requests/{user_id}/approve")
    response = client.post(f"/admin/requests/{user_id}/reject", follow_redirects=True)
    assert b"already been decided" in response.data


def test_invalid_admin_decision_action_is_not_found(client):
    admin_login(client)
    assert client.post("/admin/requests/1/delete").status_code == 404


def test_unknown_sign_up_type_is_not_found(client):
    assert client.get("/register/teacher").status_code == 404
