from clinic.doctor_repository import Doctor, DoctorRepository
from clinic.repository import AppointmentRepository


def make_doctors():
    conn = AppointmentRepository(":memory:").conn
    docs = DoctorRepository(conn)
    docs.seed_if_empty()
    return docs


def test_seed_adds_sample_doctors_once():
    docs = make_doctors()
    docs.seed_if_empty()
    assert len(docs.list_all()) == 4


def test_search_by_specialty():
    assert [d.name for d in make_doctors().search("cardio")] == ["Dr. Karim"]


def test_search_by_name():
    assert [d.name for d in make_doctors().search("Ayesha")] == ["Dr. Ayesha Rahman"]


def test_empty_search_returns_all_doctors():
    assert len(make_doctors().search("   ")) == 4


def test_get_by_name_returns_none_for_unknown_doctor():
    assert make_doctors().get_by_name("Dr. Nobody") is None


def test_time_list_splits_and_trims_slots():
    doc = Doctor(None, "Dr. X", "Test", "Clinic", "09:00, 10:00 ,")
    assert doc.time_list == ["09:00", "10:00"]


def test_search_treats_wildcards_literally():
    # Regression test: "%" and "_" used to match every doctor (found by Hypothesis).
    docs = make_doctors()
    assert docs.search("%") == []
    assert docs.search("_") == []
