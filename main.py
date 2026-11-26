from clinic.appointment import AppointmentFactory
from clinic.booking_service import BookingService
from clinic.notifier import ConsoleNotifier
from clinic.repository import AppointmentRepository


def main():
    service = BookingService(AppointmentRepository("clinic.db"), ConsoleNotifier())
    try:
        service.book(AppointmentFactory.create("Rahim", "Dr. Karim", "10:00"))
    except ValueError as e:
        print(f"Not booked: {e}")


if __name__ == "__main__":
    main()
