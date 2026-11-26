"""Property-based tests (Hypothesis, new tool).

Instead of one hand-picked example, Hypothesis generates many inputs and checks that
a rule holds for all of them. If it finds a failing input, it shrinks it to the simplest one.
"""
import string

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from clinic.appointment import AppointmentFactory
from clinic.booking_service import BookingService
from clinic.doctor_repository import DoctorRepository
from clinic.notifier import ConsoleNotifier
from clinic.repository import AppointmentRepository

NAMES = st.text(alphabet=string.ascii_letters + " .", min_size=1, max_size=20).filter(
    lambda s: s.strip()
)
SLOTS = st.from_regex(r"[0-2][0-9]:[0-5][0-9]", fullmatch=True)


@settings(max_examples=100, deadline=None)
@given(patient=NAMES, doctor=NAMES, time=SLOTS)
def test_same_doctor_and_time_can_never_be_booked_twice(patient, doctor, time):
    repo = AppointmentRepository(":memory:")
    service = BookingService(repo, ConsoleNotifier())
    service.book(AppointmentFactory.create(patient, doctor, time))
    with pytest.raises(ValueError):
        service.book(AppointmentFactory.create(patient, doctor, time))
    assert len(repo.list_all()) == 1


@settings(max_examples=200, deadline=None)
@given(blank=st.text(alphabet=" \t\n", min_size=0, max_size=10), doctor=NAMES)
def test_blank_patient_is_always_rejected(blank, doctor):
    # Whitespace-only names are not real names, so the factory must reject them.
    with pytest.raises(ValueError):
        AppointmentFactory.create(blank, doctor, "10:00")


@settings(max_examples=200, deadline=None)
@given(term=st.text(alphabet=string.ascii_letters + " %_", min_size=1, max_size=4))
def test_search_results_always_contain_the_term(term):
    conn = AppointmentRepository(":memory:").conn
    docs = DoctorRepository(conn)
    docs.seed_if_empty()
    needle = term.strip()
    if not needle:
        return
    for doc in docs.search(term):
        haystack = (doc.name + " " + doc.specialty).lower()
        assert needle.lower() in haystack, f"{doc.name!r} returned for search {term!r}"
