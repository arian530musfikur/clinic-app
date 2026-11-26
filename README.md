# CareSlot: Clinic Appointment Booking

A web application for finding doctors and booking appointments. Built with Python, Flask,
SQLite, and pytest, following an Incremental process model.

## Features
- Three sign-up types: Patient (active at once), Doctor and Admin (wait for admin approval).
- Login tabs for Patient, Doctor, and Admin. The server checks the role and the approval status.
- Doctor sign-up creates a profile with specialty, clinic, and checkup times. Admin approves it.
- Doctors edit their own profile. Admins edit any doctor profile and add doctors directly.
- Admin page: approve or reject requests, edit doctor profiles, add doctors with optional logins.
- Passwords are stored as hashes.
- Search doctors by name or specialty, and see free time slots.
- Patients book, see their own appointments, and cancel a booking.
- Doctors see only their own patients (My patients).
- Admin page: add a doctor profile with free times and an optional doctor login.
- Double-booking and unknown-doctor checks.
- Confirmation and cancellation messages (printed to the terminal, pluggable).

Demo doctor logins: karim, ayesha, imran, nusrat (password doctor123).
Demo admin login: admin (password admin123).
Patients create their own accounts on the Create account page.

## Design patterns
- **Factory** (creational): `AppointmentFactory` and `create_app()`.
- **Repository** (structural): `AppointmentRepository`, `DoctorRepository`, `UserRepository` hide SQLite.
- **Decorator** (structural): `login_required(role)` protects pages by role.
- **Strategy** (behavioral): `Notifier` and `ConsoleNotifier`.
- **Dependency injection**: `BookingService` receives its repository and notifier.

## Setup
```bash
python -m venv venv
venv\Scripts\activate            # Windows
source venv/bin/activate         # Mac/Linux
python -m pip install -r requirements.txt
```

## Run the website
```bash
python app.py
```
Open http://127.0.0.1:5000 in your browser.
If you have an old `clinic.db` from earlier versions, delete it once so the doctor list is created.

## Run the tests
```bash
python -m pytest -v
python -m pytest --cov=clinic --cov-report=term-missing
```

## Check code style (Ruff)
```bash
python -m ruff check .
```

## Browser test (optional)
Start `python app.py` in one terminal, then in another run (Windows):
```bash
set RUN_SELENIUM=1
python -m pytest tests/test_selenium.py -v
```

## Test layers
- Unit tests (Factory, Repository, rules), mock tests (BookingService), web tests (routes and access control),
  property tests (Hypothesis), persistence and migration tests (tmp_path), and one optional browser test (Selenium).

## Git and submission
See `docs/SUBMISSION_GUIDE.md` for branches, pull requests, the merge conflict steps, and screenshots.

## Run the terminal version
```bash
python main.py
```
