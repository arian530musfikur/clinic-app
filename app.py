import functools

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from clinic.appointment import AppointmentFactory
from clinic.auth import AuthService
from clinic.booking_service import BookingService
from clinic.doctor_repository import DoctorRepository
from clinic.doctor_service import DoctorService
from clinic.notifier import ConsoleNotifier
from clinic.repository import AppointmentRepository
from clinic.user import ADMIN, APPROVED, DOCTOR, PATIENT, PENDING, ROLES
from clinic.user_repository import UserRepository

TIME_SLOTS = [f"{hour:02d}:00" for hour in range(9, 17)]

# Demo logins for the student demo. Patients and doctors can also sign up on the website.
DEMO_DOCTOR_ACCOUNTS = {
    "karim": "Dr. Karim",
    "ayesha": "Dr. Ayesha Rahman",
    "imran": "Dr. Imran Hossain",
    "nusrat": "Dr. Nusrat Jahan",
}
DEMO_PASSWORD = "doctor123"
DEMO_ADMIN = ("admin", "admin123")
# Demo passwords are for the student demo only; never use them in a real system.


def create_app(repo=None):
    """Factory for the web app. Tests pass an in-memory repository."""
    app = Flask(__name__)
    app.secret_key = "dev-only-change-me"

    appointments = repo or AppointmentRepository("clinic.db")
    doctors = DoctorRepository(appointments.conn)
    users = UserRepository(appointments.conn)
    auth = AuthService(users)
    doctor_service = DoctorService(doctors, auth)
    service = BookingService(appointments, ConsoleNotifier())

    doctors.seed_if_empty()
    if users.get_by_username(DEMO_ADMIN[0]) is None:
        auth.create_admin_account(DEMO_ADMIN[0], DEMO_ADMIN[1], "Clinic Administrator")
    for username, doctor_name in DEMO_DOCTOR_ACCOUNTS.items():
        doctor = doctors.get_by_name(doctor_name)
        if doctor is None:
            continue
        user = users.get_by_username(username)
        if user is None:
            user = auth.create_doctor_account(username, DEMO_PASSWORD, doctor.name)
        if doctor.user_id is None:
            doctors.link_user(doctor.id, user.id)

    def current_user():
        user_id = session.get("user_id")
        return users.get(user_id) if user_id else None

    def login_required(role=None):
        """Decorator (structural): checks the user is logged in and has the required role."""

        def decorator(view):
            @functools.wraps(view)
            def wrapper(*args, **kwargs):
                user = current_user()
                if user is None:
                    flash("Please log in first.", "error")
                    return redirect(url_for("login"))
                if role and user.role != role:
                    abort(403)
                return view(*args, **kwargs)

            return wrapper

        return decorator

    @app.context_processor
    def inject_globals():
        user = current_user()
        pending = len(users.list_by_status(PENDING)) if user and user.role == ADMIN else 0
        return {"current_user": user, "pending_count": pending}

    @app.route("/")
    def index():
        query = request.args.get("q", "")
        user = current_user()
        stats = []
        if user and user.role == PATIENT:
            stats = [
                {"label": "My bookings", "value": len(appointments.list_by_patient_id(user.id))},
                {"label": "Doctors available", "value": len(doctors.list_approved())},
            ]
        elif user and user.role == DOCTOR:
            doctor = doctors.get_by_user_id(user.id)
            if doctor is not None:
                stats = [
                    {
                        "label": "Patients booked",
                        "value": len(appointments.list_by_doctor(doctor.name)),
                    },
                    {"label": "Checkup times", "value": len(doctor.time_list)},
                ]
        elif user and user.role == ADMIN:
            stats = [
                {"label": "Pending requests", "value": len(users.list_by_status(PENDING))},
                {"label": "Doctors", "value": len(doctors.list_all())},
                {"label": "Bookings", "value": len(appointments.list_all())},
            ]
        return render_template(
            "index.html",
            doctors=doctors.search(query),
            all_doctors=doctors.list_approved(),
            query=query,
            slots=TIME_SLOTS,
            stats=stats,
        )

    @app.route("/register")
    def register_choice():
        return render_template("register_choice.html")

    @app.route("/register/<role>", methods=["GET", "POST"])
    def register(role):
        if role not in ROLES:
            abort(404)
        if request.method == "POST":
            form = request.form
            username = form.get("username", "")
            password = form.get("password", "")
            full_name = form.get("full_name", "")
            try:
                if role == PATIENT:
                    user = auth.register_patient(username, password, full_name)
                    session["user_id"] = user.id
                    flash(f"Welcome, {user.full_name}. Your account is ready.", "ok")
                    return redirect(url_for("index"))
                if role == DOCTOR:
                    doctor_service.request_doctor_signup(
                        username, password, full_name,
                        form.get("specialty", ""), form.get("hospital", ""), form.get("times", ""),
                    )
                    flash(
                        "Doctor request sent. An admin must approve it before you log in.", "ok"
                    )
                    return redirect(url_for("login", role=DOCTOR))
                auth.register(ADMIN, username, password, full_name)
                flash("Admin request sent. An existing admin must approve it first.", "ok")
                return redirect(url_for("login", role=ADMIN))
            except ValueError as e:
                flash(str(e), "error")
        return render_template("register.html", role=role)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        selected = request.values.get("role") or PATIENT
        if request.method == "POST":
            try:
                user = auth.login(
                    request.form.get("username", ""),
                    request.form.get("password", ""),
                    request.form.get("role") or None,
                )
                session["user_id"] = user.id
                flash(f"Welcome back, {user.full_name}.", "ok")
                return redirect(url_for("index"))
            except ValueError as e:
                flash(str(e), "error")
        return render_template("auth.html", selected_role=selected)

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You are logged out.", "ok")
        return redirect(url_for("index"))

    @app.post("/book")
    @login_required(PATIENT)
    def book():
        user = current_user()
        try:
            appt = AppointmentFactory.create(
                user.full_name,
                request.form.get("doctor", ""),
                request.form.get("time", ""),
                patient_id=user.id,
            )
            doctor = doctors.get_by_name(appt.doctor)
            if doctor is None or doctor.status != APPROVED:
                raise ValueError("Choose a doctor from the list.")
            if appt.time not in doctor.time_list:
                raise ValueError("That time is not free for this doctor.")
            service.book(appt)
            flash(f"Booked {appt.doctor} at {appt.time}. Confirmation sent.", "ok")
        except ValueError as e:
            flash(str(e), "error")
        return redirect(url_for("index"))

    @app.route("/my-appointments")
    @login_required(PATIENT)
    def my_appointments():
        return render_template(
            "my_appointments.html",
            appointments=appointments.list_by_patient_id(current_user().id),
        )

    @app.post("/appointments/<int:appt_id>/cancel")
    @login_required(PATIENT)
    def cancel_appointment(appt_id):
        try:
            service.cancel(appt_id, current_user().id)
            flash("Appointment cancelled. The slot is free again.", "ok")
        except ValueError as e:
            flash(str(e), "error")
        return redirect(url_for("my_appointments"))

    @app.route("/my-patients")
    @login_required(DOCTOR)
    def my_patients():
        doctor = doctors.get_by_user_id(current_user().id)
        if doctor is None:
            abort(404)
        return render_template(
            "doctor.html",
            doctor=doctor,
            appointments=appointments.list_by_doctor(doctor.name),
        )

    @app.route("/doctor/profile", methods=["GET", "POST"])
    @login_required(DOCTOR)
    def doctor_profile():
        doctor = doctors.get_by_user_id(current_user().id)
        if doctor is None:
            abort(404)
        if request.method == "POST":
            try:
                doctor_service.update_profile(
                    doctor.id,
                    request.form.get("specialty", ""),
                    request.form.get("hospital", ""),
                    request.form.get("times", ""),
                )
                flash("Profile saved. Patients now see your new details.", "ok")
                return redirect(url_for("doctor_profile"))
            except ValueError as e:
                flash(str(e), "error")
            doctor = doctors.get_by_user_id(current_user().id)
        return render_template("doctor_profile.html", doctor=doctor)

    @app.route("/admin")
    @login_required(ADMIN)
    def admin_page():
        requests = []
        for user in users.list_by_status(PENDING):
            profile = doctors.get_by_user_id(user.id) if user.role == DOCTOR else None
            requests.append((user, profile))
        return render_template(
            "admin.html",
            requests=requests,
            doctors=doctors.list_all(),
            booking_count=len(appointments.list_all()),
        )

    @app.post("/admin/requests/<int:user_id>/<action>")
    @login_required(ADMIN)
    def decide_request(user_id, action):
        if action not in ("approve", "reject"):
            abort(404)
        try:
            doctor_service.decide(user_id, approve=(action == "approve"))
            flash("Request approved." if action == "approve" else "Request rejected.", "ok")
        except ValueError as e:
            flash(str(e), "error")
        return redirect(url_for("admin_page"))

    @app.post("/admin/doctors")
    @login_required(ADMIN)
    def add_doctor():
        form = request.form
        try:
            doctor = doctor_service.add_doctor(
                form.get("name", ""),
                form.get("specialty", ""),
                form.get("hospital", ""),
                form.get("times", ""),
                form.get("username", ""),
                form.get("password", ""),
            )
            extra = " A doctor login was created." if form.get("username", "").strip() else ""
            flash(f"Added {doctor.name}.{extra}", "ok")
        except ValueError as e:
            flash(str(e), "error")
        return redirect(url_for("admin_page"))

    @app.post("/admin/doctors/<int:doctor_id>/edit")
    @login_required(ADMIN)
    def edit_doctor(doctor_id):
        try:
            doctor_service.update_profile(
                doctor_id,
                request.form.get("specialty", ""),
                request.form.get("hospital", ""),
                request.form.get("times", ""),
            )
            flash("Doctor profile updated.", "ok")
        except ValueError as e:
            flash(str(e), "error")
        return redirect(url_for("admin_page"))

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
