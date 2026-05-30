from backend.services.mail.mail_chat_account_guard_store import (
    PendingMailAccountChoice,
    get_pending_account_choice,
    pop_pending_account_choice,
    set_pending_account_choice,
)


def test_mail_chat_account_guard_roundtrip():
    chat_id = 7654321
    pending = PendingMailAccountChoice(
        action="list_latest",
        accounts=["a@example.com", "b@example.com"],
        payload={"count": 4},
    )
    set_pending_account_choice(chat_id, pending)
    loaded = get_pending_account_choice(chat_id)
    assert loaded is not None
    assert loaded.action == "list_latest"
    assert len(loaded.accounts) == 2
    popped = pop_pending_account_choice(chat_id)
    assert popped is not None
    assert get_pending_account_choice(chat_id) is None

