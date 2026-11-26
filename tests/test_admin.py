import pytest

from clinic.doctor_repository import DoctorRepository
from clinic.doctor_service import DoctorService
from tests.helpers import book, login, logout, register


def admin_login(client):
    return login(client, "admin", "admin123", role="admin")


def new_doctor_form(**overrides):
    form = {
        "name": "Dr. Test Doc",
        "specialty": "Neurology",
        "hospital": "Test Hospital",
        "times": "09:00,10:00",
        "username": "",
        "password": "",
    }
    form.update(overrides)
    return form


def test_admin_can_open_admin_page(client):
    admin_login(client)
    response = client.get("/admin")
    assert response.status_code == 200
    assert b"Add a doctor" in response.data


def test_patient_cannot_open_admin_page(client):
    register(client)
    assert client.get("/admin").status_code == 403


def test_anonymous_user_is_sent_to_login_for_admin_page(client):
    assert client.get("/admin").status_code == 302


def test_admin_login_tab_rejects_patient_account(client):
    register(client)
    logout(client)
    response = login(client, "rahim", "secret123", role="admin")
    assert b"does not have the admin role" in response.data


def test_admin_adds_doctor_who_can_then_log_in(client):
    admin_login(client)
    response = client.post(
        "/admin/doctors",
        data=new_doctor_form(username="testdoc", password="doctor123"),
        follow_redirects=True,
    )
    assert b"Added Dr. Test Doc" in response.data
    assert b"A doctor login was created" in response.data

    logout(client)
    response = login(client, "testdoc", "doctor123", role="doctor")
    assert b"Welcome back" in response.data


def test_new_doctor_appears_in_search(client):
    admin_login(client)
    client.post("/admin/doctors", data=new_doctor_form(), follow_redirects=True)
    response = client.get("/", query_string={"q": "Neurology"})
    assert b"Dr. Test Doc" in response.data


def test_duplicate_doctor_name_is_rejected(client):
    admin_login(client)
    response = client.post(
        "/admin/doctors", data=new_doctor_form(name="Dr. Karim"), follow_redirects=True
    )
    assert b"already exists" in response.data


@pytest.mark.parametrize(
    ("times", "message"),
    [
        ("", b"Enter at least one checkup time"),
        (" , ", b"Enter at least one checkup time"),
        ("9am", b"Times must look like 09:00"),
        ("25:00", b"Times must look like 09:00"),
    ],
)
def test_invalid_free_times_are_rejected(client, times, message):
    admin_login(client)
    response = client.post(
        "/admin/doctors", data=new_doctor_form(name=f"Dr. {len(times)}", times=times),
        follow_redirects=True,
    )
    assert message in response.data


def test_booking_outside_doctor_free_times_is_rejected(client, repo):
    register(client)
    response = book(client, doctor="Dr. Karim", time="16:00", follow=True)
    assert b"not free for this doctor" in response.data
    assert not repo.is_slot_taken("Dr. Karim", "16:00")


def test_seeded_admin_account_exists(client, repo):
    from clinic.user_repository import UserRepository

    assert UserRepository(repo.conn).get_by_username("admin").role == "admin"


def test_doctor_service_rolls_back_nothing_when_login_is_invalid(repo, auth, doctors):
    service = DoctorService(doctors, auth)
    auth.register_patient("rahim", "secret123", "Rahim Uddin")
    with pytest.raises(ValueError, match="already taken"):
        service.add_doctor(
            "Dr. Y", "Oncology", "Clinic", "09:00", username="rahim", password="secret123"
        )
    assert DoctorRepository(repo.conn).get_by_name("Dr. Y") is None


def test_doctor_service_creates_doctor_with_linked_login(auth, doctors):
    service = DoctorService(doctors, auth)
    doc = service.add_doctor(
        "Dr. X", "Oncology", "Clinic", "09:00", username="drx", password="secret123"
    )
    assert doctors.get_by_user_id(auth.users.get_by_username("drx").id).id == doc.id


@pytest.mark.parametrize(
    ("name", "specialty", "hospital"),
    [("", "Oncology", "Clinic"), ("Dr. Z", " ", "Clinic"), ("Dr. Z", "Oncology", "")],
)
def test_doctor_profile_fields_are_required(auth, doctors, name, specialty, hospital):
    with pytest.raises(ValueError, match="required"):
        DoctorService(doctors, auth).add_doctor(name, specialty, hospital, "09:00")


def test_doctor_login_password_must_be_long_enough(auth, doctors):
    with pytest.raises(ValueError, match="at least 6"):
        DoctorService(doctors, auth).add_doctor(
            "Dr. W", "Oncology", "Clinic", "09:00", username="drw", password="123"
        )


def test_doctor_login_password_must_be_long_enough_when_admin_adds_doctor(auth, doctors):
    with pytest.raises(ValueError, match="at least 6"):
        DoctorService(doctors, auth).add_doctor(
            "Dr. V", "Oncology", "Clinic", "09:00", username="drv", password="12"
        )


def test_decision_on_unknown_request_is_rejected(auth, doctors):
    with pytest.raises(ValueError, match="Request not found"):
        DoctorService(doctors, auth).decide(999, approve=True)


def test_admin_profile_edit_needs_specialty_and_clinic(client, doctors):
    admin_login(client)
    karim = doctors.get_by_name("Dr. Karim")
    response = client.post(
        f"/admin/doctors/{karim.id}/edit",
        data={"specialty": " ", "hospital": "New Wing", "times": "13:00"},
        follow_redirects=True,
    )
    assert b"Specialty and clinic are required" in response.data
    assert doctors.get(karim.id).specialty == "Cardiology"
