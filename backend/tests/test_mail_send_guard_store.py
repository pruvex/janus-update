from backend.services.mail.mail_send_guard_store import (
    PendingMailSend,
    get_pending_mail_send,
    pop_pending_mail_send,
    set_pending_mail_send,
)


def test_mail_send_guard_store_roundtrip():
    chat_id = 987654
    pending = PendingMailSend(
        to="alice@example.com",
        subject="Termin",
        body="Bitte bestaetige den Termin um 10 Uhr.",
    )
    set_pending_mail_send(chat_id, pending)
    loaded = get_pending_mail_send(chat_id)
    assert loaded is not None
    assert loaded.to == "alice@example.com"
    assert loaded.subject == "Termin"

    popped = pop_pending_mail_send(chat_id)
    assert popped is not None
    assert popped.body.startswith("Bitte bestaetige")
    assert get_pending_mail_send(chat_id) is None

