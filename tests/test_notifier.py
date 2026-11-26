from clinic.notifier import ConsoleNotifier


def test_console_notifier_prints_the_message(capsys):  # capsys: pytest captures printed output
    ConsoleNotifier().send("Rahim", "Appointment confirmed")
    assert capsys.readouterr().out == "[to Rahim] Appointment confirmed\n"
