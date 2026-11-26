from abc import ABC, abstractmethod


class Notifier(ABC):
    """Strategy (behavioral) interface. Any notification method can be plugged in."""

    @abstractmethod
    def send(self, to: str, message: str) -> None: ...


class ConsoleNotifier(Notifier):
    """Demo strategy: prints the message.

    Add EmailNotifier or SMSNotifier without changing BookingService.
    """

    def send(self, to: str, message: str) -> None:
        print(f"[to {to}] {message}")
