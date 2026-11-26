"""Shared pytest fixtures (pytest feature: fixtures remove repeated setup code).

Each test that asks for `repo`, `client`, or `auth` gets a fresh, isolated in-memory
database, so tests never affect each other.
"""

import pytest

from app import create_app
from clinic.auth import AuthService
from clinic.doctor_repository import DoctorRepository
from clinic.repository import AppointmentRepository
from clinic.user_repository import UserRepository


@pytest.fixture
def repo():
    return AppointmentRepository(":memory:")


@pytest.fixture
def client(repo):
    return create_app(repo).test_client()


@pytest.fixture
def auth(repo):
    return AuthService(UserRepository(repo.conn))


@pytest.fixture
def doctors(repo):
    docs = DoctorRepository(repo.conn)
    docs.seed_if_empty()
    return docs
