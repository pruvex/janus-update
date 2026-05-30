import base64
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

import backend.api.routers.mail as mail_router
from backend.data.schemas_mail import MailConnectionStatus
from backend.dependencies import api_key_auth
from backend.main import app
from backend.services.mail.mail_service import MailService, MailServiceError


client = TestClient(app)


def _creds(valid=True, expired=False, refresh_token=None, scopes=None):
    return SimpleNamespace(
        valid=valid,
        expired=expired,
        refresh_token=refresh_token,
        scopes=scopes or [],
    )


def test_connection_status_disconnected_when_token_missing():
    service = MailService()
    with patch("backend.services.mail.mail_service.keyring.get_password", return_value=None):
        status = service.get_connection_status()
    assert status.status == "disconnected"
    assert "No Gmail token" in (status.error_message or "")


def test_connection_status_missing_scope():
    service = MailService()
    token_json = '{"client_id":"test-client"}'
    with (
        patch("backend.services.mail.mail_service.keyring.get_password", return_value=token_json),
        patch(
            "backend.services.mail.mail_service.Credentials.from_authorized_user_info",
            return_value=_creds(valid=True, scopes=["https://www.googleapis.com/auth/gmail.readonly"]),
        ),
    ):
        status = service.get_connection_status()
    assert status.status == "missing_scope"
    assert "Missing required Gmail scopes" in (status.error_message or "")


def test_connection_status_connected_for_refreshable_token():
    service = MailService()
    token_json = '{"client_id":"test-client"}'
    with (
        patch("backend.services.mail.mail_service.keyring.get_password", return_value=token_json),
        patch(
            "backend.services.mail.mail_service.Credentials.from_authorized_user_info",
            return_value=_creds(
                valid=False,
                expired=True,
                refresh_token="refresh-token",
                scopes=[
                    "https://www.googleapis.com/auth/calendar",
                    "https://www.googleapis.com/auth/gmail.readonly",
                    "https://www.googleapis.com/auth/gmail.send",
                ],
            ),
        ),
    ):
        status = service.get_connection_status()
    assert status.status == "connected"
    assert status.account_hint == "test-client"


def test_connection_status_sync_error_for_unusable_token():
    service = MailService()
    token_json = '{"client_id":"test-client"}'
    with (
        patch("backend.services.mail.mail_service.keyring.get_password", return_value=token_json),
        patch(
            "backend.services.mail.mail_service.Credentials.from_authorized_user_info",
            return_value=_creds(
                valid=False,
                expired=False,
                refresh_token=None,
                scopes=[
                    "https://www.googleapis.com/auth/calendar",
                    "https://www.googleapis.com/auth/gmail.readonly",
                    "https://www.googleapis.com/auth/gmail.send",
                ],
            ),
        ),
    ):
        status = service.get_connection_status()
    assert status.status == "sync_error"


def test_mail_sync_status_endpoint_uses_service_contract():
    app.dependency_overrides[api_key_auth] = lambda: None
    try:
        expected = MailConnectionStatus(status="disconnected", error_message="No Gmail token configured.")
        with patch.object(mail_router._mail_service, "get_connection_status", return_value=expected):
            response = client.get("/api/mail/sync/status")
    finally:
        app.dependency_overrides.pop(api_key_auth, None)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "disconnected"
    assert body["provider"] == "gmail"
    assert "No Gmail token" in body.get("error_message", "")


def test_mail_sync_status_endpoint_returns_500_on_unexpected_error():
    app.dependency_overrides[api_key_auth] = lambda: None
    try:
        with patch.object(mail_router._mail_service, "get_connection_status", side_effect=RuntimeError("boom")):
            response = client.get("/api/mail/sync/status")
    finally:
        app.dependency_overrides.pop(api_key_auth, None)

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to resolve mail connection status."


def test_list_inbox_threads_returns_compact_rows():
    service = MailService()
    token_json = '{"client_id":"test-client"}'

    class _MessagesApi:
        def list(self, **kwargs):
            class _Req:
                def execute(self_nonlocal):
                    assert kwargs["labelIds"] == ["INBOX"]
                    assert kwargs["maxResults"] == 2
                    return {"messages": [{"id": "m1"}, {"id": "m2"}], "nextPageToken": "nxt"}

            return _Req()

        def get(self, **kwargs):
            class _Req:
                def execute(self_nonlocal):
                    return {
                        "labelIds": ["INBOX", "UNREAD"] if kwargs["id"] == "m1" else ["INBOX"],
                        "payload": {
                            "headers": [
                                {"name": "From", "value": "sender@example.com"},
                                {"name": "Subject", "value": f"Subject {kwargs['id']}"},
                                {"name": "Date", "value": "Thu, 28 May 2026 10:00:00 +0000"},
                            ]
                        },
                        "snippet": f"Snippet {kwargs['id']}",
                    }

            return _Req()

    class _UsersApi:
        def messages(self):
            return _MessagesApi()

    class _GmailApi:
        def users(self):
            return _UsersApi()

    with (
        patch("backend.services.mail.mail_service.keyring.get_password", return_value=token_json),
        patch(
            "backend.services.mail.mail_service.Credentials.from_authorized_user_info",
            return_value=_creds(
                valid=True,
                scopes=[
                    "https://www.googleapis.com/auth/calendar",
                    "https://www.googleapis.com/auth/gmail.readonly",
                    "https://www.googleapis.com/auth/gmail.send",
                ],
            ),
        ),
        patch("backend.services.mail.mail_service.build", return_value=_GmailApi()),
    ):
        result = service.list_inbox_threads(max_results=2)

    assert result.provider == "gmail"
    assert len(result.threads) == 2
    assert result.threads[0].id == "m1"
    assert result.threads[0].subject == "Subject m1"
    assert result.threads[0].unread is True
    assert result.threads[1].unread is False
    assert result.next_page_token == "nxt"


def test_list_threads_supports_sent_folder_label():
    service = MailService()
    token_json = '{"client_id":"test-client"}'

    class _MessagesApi:
        def list(self, **kwargs):
            class _Req:
                def execute(self_nonlocal):
                    assert kwargs["labelIds"] == ["SENT"]
                    return {"messages": []}

            return _Req()

        def get(self, **kwargs):
            class _Req:
                def execute(self_nonlocal):
                    return {"payload": {"headers": []}, "snippet": ""}

            return _Req()

    class _UsersApi:
        def messages(self):
            return _MessagesApi()

    class _GmailApi:
        def users(self):
            return _UsersApi()

    with (
        patch("backend.services.mail.mail_service.keyring.get_password", return_value=token_json),
        patch(
            "backend.services.mail.mail_service.Credentials.from_authorized_user_info",
            return_value=_creds(
                valid=True,
                scopes=[
                    "https://www.googleapis.com/auth/calendar",
                    "https://www.googleapis.com/auth/gmail.readonly",
                    "https://www.googleapis.com/auth/gmail.send",
                ],
            ),
        ),
        patch("backend.services.mail.mail_service.build", return_value=_GmailApi()),
    ):
        result = service.list_inbox_threads(folder="sent")

    assert result.provider == "gmail"
    assert result.threads == []


def test_list_threads_rejects_unknown_folder():
    service = MailService()
    token_json = '{"client_id":"test-client"}'
    with (
        patch("backend.services.mail.mail_service.keyring.get_password", return_value=token_json),
        patch(
            "backend.services.mail.mail_service.Credentials.from_authorized_user_info",
            return_value=_creds(
                valid=True,
                scopes=[
                    "https://www.googleapis.com/auth/calendar",
                    "https://www.googleapis.com/auth/gmail.readonly",
                    "https://www.googleapis.com/auth/gmail.send",
                ],
            ),
        ),
    ):
        try:
            service.list_inbox_threads(folder="archive")
            assert False, "Expected MailServiceError"
        except MailServiceError as exc:
            assert exc.status_code == 400
            assert "Unsupported mail folder" in exc.message


def test_mail_threads_endpoint_uses_service_contract():
    app.dependency_overrides[api_key_auth] = lambda: None
    try:
        with patch.object(
            mail_router._mail_service,
            "list_inbox_threads",
            return_value={
                "provider": "gmail",
                "threads": [
                    {
                        "id": "m1",
                        "from_display": "sender@example.com",
                        "subject": "Hi",
                        "date": "Thu, 28 May 2026 10:00:00 +0000",
                        "snippet": "Test",
                    }
                ],
                "next_page_token": None,
            },
        ):
            response = client.get("/api/mail/threads?q=test&max_results=10")
    finally:
        app.dependency_overrides.pop(api_key_auth, None)

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "gmail"
    assert len(body["threads"]) == 1
    assert body["threads"][0]["id"] == "m1"


def test_mail_threads_endpoint_returns_service_error():
    app.dependency_overrides[api_key_auth] = lambda: None
    try:
        with patch.object(
            mail_router._mail_service,
            "list_inbox_threads",
            side_effect=mail_router.MailServiceError("No Gmail token configured.", status_code=400),
        ):
            response = client.get("/api/mail/threads")
    finally:
        app.dependency_overrides.pop(api_key_auth, None)

    assert response.status_code == 400
    assert response.json()["detail"] == "No Gmail token configured."


def test_mail_threads_endpoint_passes_folder_param():
    app.dependency_overrides[api_key_auth] = lambda: None
    try:
        with patch.object(
            mail_router._mail_service,
            "list_inbox_threads",
            return_value={
                "provider": "gmail",
                "threads": [],
                "next_page_token": None,
            },
        ) as mocked:
            response = client.get("/api/mail/threads?folder=sent&max_results=5")
    finally:
        app.dependency_overrides.pop(api_key_auth, None)

    assert response.status_code == 200
    mocked.assert_called_once()
    assert mocked.call_args.kwargs["folder"] == "sent"


def test_get_message_detail_returns_full_payload():
    service = MailService()
    token_json = '{"client_id":"test-client"}'

    class _MessagesApi:
        def get(self, **kwargs):
            class _Req:
                def execute(self_nonlocal):
                    return {
                        "snippet": "Kurzvorschau",
                        "payload": {
                            "headers": [
                                {"name": "From", "value": "alice@example.com"},
                                {"name": "To", "value": "bob@example.com"},
                                {"name": "Subject", "value": "Betreff"},
                                {"name": "Date", "value": "Thu, 28 May 2026 10:00:00 +0000"},
                                {"name": "Message-ID", "value": "<abc@example.com>"},
                                {"name": "References", "value": "<old@example.com>"},
                            ],
                            "parts": [
                                {
                                    "mimeType": "text/plain",
                                    "body": {"data": "SGFsbG8gV2VsdA=="},
                                },
                                {
                                    "mimeType": "application/pdf",
                                    "filename": "test.pdf",
                                    "body": {"attachmentId": "att-1", "size": 1234},
                                }
                            ],
                            "mimeType": "multipart/mixed",
                        },
                    }

            return _Req()

    class _UsersApi:
        def messages(self):
            return _MessagesApi()

    class _GmailApi:
        def users(self):
            return _UsersApi()

    with (
        patch("backend.services.mail.mail_service.keyring.get_password", return_value=token_json),
        patch(
            "backend.services.mail.mail_service.Credentials.from_authorized_user_info",
            return_value=_creds(
                valid=True,
                scopes=[
                    "https://www.googleapis.com/auth/calendar",
                    "https://www.googleapis.com/auth/gmail.readonly",
                    "https://www.googleapis.com/auth/gmail.send",
                ],
            ),
        ),
        patch("backend.services.mail.mail_service.build", return_value=_GmailApi()),
    ):
        result = service.get_message_detail("m42")

    assert result.id == "m42"
    assert result.from_display == "alice@example.com"
    assert result.to_display == "bob@example.com"
    assert result.subject == "Betreff"
    assert result.body_text == "Hallo Welt"
    assert result.message_id_header == "<abc@example.com>"
    assert result.references_header == "<old@example.com>"
    assert len(result.attachments) == 1
    assert result.attachments[0].attachment_id == "att-1"


def test_download_attachment_returns_payload():
    service = MailService()
    token_json = '{"client_id":"test-client"}'

    class _AttachmentsApi:
        def get(self, **kwargs):
            class _Req:
                def execute(self_nonlocal):
                    assert kwargs["id"] == "att-1"
                    return {"data": "aGVsbG8="}

            return _Req()

    class _MessagesApi:
        def get(self, **kwargs):
            class _Req:
                def execute(self_nonlocal):
                    return {
                        "payload": {
                            "parts": [
                                {
                                    "filename": "hello.txt",
                                    "mimeType": "text/plain",
                                    "body": {"attachmentId": "att-1", "size": 5},
                                }
                            ]
                        }
                    }

            return _Req()

        def attachments(self):
            return _AttachmentsApi()

    class _UsersApi:
        def messages(self):
            return _MessagesApi()

    class _GmailApi:
        def users(self):
            return _UsersApi()

    with (
        patch("backend.services.mail.mail_service.keyring.get_password", return_value=token_json),
        patch(
            "backend.services.mail.mail_service.Credentials.from_authorized_user_info",
            return_value=_creds(
                valid=True,
                scopes=[
                    "https://www.googleapis.com/auth/calendar",
                    "https://www.googleapis.com/auth/gmail.readonly",
                    "https://www.googleapis.com/auth/gmail.send",
                ],
            ),
        ),
        patch("backend.services.mail.mail_service.build", return_value=_GmailApi()),
    ):
        payload = service.download_attachment("m42", "att-1")
    assert payload["filename"] == "hello.txt"
    assert payload["mime_type"] == "text/plain"
    assert payload["content"] == b"hello"


def test_mail_message_detail_endpoint_uses_service_contract():
    app.dependency_overrides[api_key_auth] = lambda: None
    try:
        with patch.object(
            mail_router._mail_service,
            "get_message_detail",
            return_value={
                "id": "m1",
                "from_display": "a@example.com",
                "to_display": "b@example.com",
                "subject": "Hi",
                "date": "Thu, 28 May 2026 10:00:00 +0000",
                "snippet": "Kurz",
                "body_text": "Volltext",
            },
        ):
            response = client.get("/api/mail/messages/m1")
    finally:
        app.dependency_overrides.pop(api_key_auth, None)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "m1"
    assert body["body_text"] == "Volltext"


def test_trash_message_calls_gmail_trash():
    service = MailService()
    token_json = '{"client_id":"test-client"}'
    called = {"trash": False}

    class _MessagesApi:
        def trash(self, **kwargs):
            class _Req:
                def execute(self_nonlocal):
                    called["trash"] = True
                    assert kwargs["id"] == "m9"
                    return {}
            return _Req()

    class _UsersApi:
        def messages(self):
            return _MessagesApi()

    class _GmailApi:
        def users(self):
            return _UsersApi()

    with (
        patch("backend.services.mail.mail_service.keyring.get_password", return_value=token_json),
        patch(
            "backend.services.mail.mail_service.Credentials.from_authorized_user_info",
            return_value=_creds(valid=True, scopes=[
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send",
            ]),
        ),
        patch("backend.services.mail.mail_service.build", return_value=_GmailApi()),
    ):
        result = service.trash_message("m9")
    assert called["trash"] is True
    assert result.ok is True
    assert result.target_folder == "trash"


def test_move_message_calls_gmail_modify():
    service = MailService()
    token_json = '{"client_id":"test-client"}'
    called = {"modify": False}

    class _MessagesApi:
        def modify(self, **kwargs):
            class _Req:
                def execute(self_nonlocal):
                    called["modify"] = True
                    assert kwargs["id"] == "m11"
                    assert "addLabelIds" in kwargs["body"]
                    return {}
            return _Req()

    class _UsersApi:
        def messages(self):
            return _MessagesApi()

    class _GmailApi:
        def users(self):
            return _UsersApi()

    with (
        patch("backend.services.mail.mail_service.keyring.get_password", return_value=token_json),
        patch(
            "backend.services.mail.mail_service.Credentials.from_authorized_user_info",
            return_value=_creds(valid=True, scopes=[
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send",
            ]),
        ),
        patch("backend.services.mail.mail_service.build", return_value=_GmailApi()),
    ):
        result = service.move_message("m11", "inbox")
    assert called["modify"] is True
    assert result.ok is True
    assert result.target_folder == "inbox"


def test_mail_disconnect_endpoint_returns_action_result():
    app.dependency_overrides[api_key_auth] = lambda: None
    try:
        with patch.object(mail_router._mail_service, "disconnect_account", return_value=None):
            response = client.post("/api/mail/disconnect")
    finally:
        app.dependency_overrides.pop(api_key_auth, None)

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["message_id"] == "account"


def test_send_message_calls_gmail_send():
    service = MailService()
    token_json = '{"client_id":"test-client"}'
    called = {"send": False}

    class _MessagesApi:
        def send(self, **kwargs):
            class _Req:
                def execute(self_nonlocal):
                    called["send"] = True
                    assert kwargs["userId"] == "me"
                    raw = kwargs["body"].get("raw")
                    assert raw
                    decoded = base64.urlsafe_b64decode(raw.encode("ascii")).decode("utf-8", errors="replace")
                    assert "To: alice@example.com" in decoded
                    return {"id": "sent-123"}

            return _Req()

    class _UsersApi:
        def messages(self):
            return _MessagesApi()

    class _GmailApi:
        def users(self):
            return _UsersApi()

    with (
        patch("backend.services.mail.mail_service.keyring.get_password", return_value=token_json),
        patch(
            "backend.services.mail.mail_service.Credentials.from_authorized_user_info",
            return_value=_creds(valid=True, scopes=[
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send",
            ]),
        ),
        patch("backend.services.mail.mail_service.build", return_value=_GmailApi()),
    ):
        result = service.send_message(
            to="alice@example.com",
            cc="",
            bcc="",
            subject="Test",
            body="Hallo",
        )
    assert called["send"] is True
    assert result.ok is True
    assert result.target_folder == "sent"


def test_send_message_includes_reply_headers_and_original_attachments():
    service = MailService()
    token_json = '{"client_id":"test-client"}'
    called = {"send": False}

    class _AttachmentsApi:
        def get(self, **kwargs):
            class _Req:
                def execute(self_nonlocal):
                    assert kwargs["id"] == "att-1"
                    return {"data": "aGVsbG8="}
            return _Req()

    class _MessagesApi:
        def get(self, **kwargs):
            class _Req:
                def execute(self_nonlocal):
                    if kwargs.get("id") == "src-1":
                        return {
                            "payload": {
                                "parts": [
                                    {
                                        "filename": "hello.txt",
                                        "mimeType": "text/plain",
                                        "body": {"attachmentId": "att-1", "size": 5},
                                    }
                                ]
                            }
                        }
                    return {"payload": {"headers": []}, "snippet": ""}
            return _Req()

        def attachments(self):
            return _AttachmentsApi()

        def send(self, **kwargs):
            class _Req:
                def execute(self_nonlocal):
                    called["send"] = True
                    raw = kwargs["body"].get("raw")
                    decoded = base64.urlsafe_b64decode(raw.encode("ascii")).decode("utf-8", errors="replace")
                    assert "In-Reply-To: <abc@example.com>" in decoded
                    assert "References: <old@example.com> <abc@example.com>" in decoded
                    assert 'filename="hello.txt"' in decoded
                    return {"id": "sent-124"}
            return _Req()

    class _UsersApi:
        def messages(self):
            return _MessagesApi()

    class _GmailApi:
        def users(self):
            return _UsersApi()

    with (
        patch("backend.services.mail.mail_service.keyring.get_password", return_value=token_json),
        patch(
            "backend.services.mail.mail_service.Credentials.from_authorized_user_info",
            return_value=_creds(valid=True, scopes=[
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send",
            ]),
        ),
        patch("backend.services.mail.mail_service.build", return_value=_GmailApi()),
    ):
        result = service.send_message(
            to="alice@example.com",
            subject="Re: Test",
            body="Antwort",
            in_reply_to="<abc@example.com>",
            references="<old@example.com> <abc@example.com>",
            source_message_id="src-1",
            include_original_attachments=True,
        )
    assert called["send"] is True
    assert result.ok is True


def test_mail_send_endpoint_uses_service_contract():
    app.dependency_overrides[api_key_auth] = lambda: None
    try:
        with patch.object(
            mail_router._mail_service,
            "send_message",
            return_value={
                "ok": True,
                "message_id": "sent-1",
                "message": "E-Mail wurde gesendet.",
                "target_folder": "sent",
            },
        ):
            response = client.post(
                "/api/mail/messages/send",
                data={"to": "alice@example.com", "subject": "Hi", "body": "Hallo", "cc": "", "bcc": ""},
            )
    finally:
        app.dependency_overrides.pop(api_key_auth, None)

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["message_id"] == "sent-1"


def test_find_latest_message_by_sender_returns_detail():
    service = MailService()
    with (
        patch.object(
            service,
            "list_inbox_threads",
            return_value=SimpleNamespace(threads=[
                SimpleNamespace(id="m1", from_display="Alice <alice@example.com>"),
                SimpleNamespace(id="m2", from_display="Bob <bob@example.com>"),
            ]),
        ),
        patch.object(
            service,
            "get_message_detail",
            return_value=SimpleNamespace(
                id="m2",
                from_display="Bob <bob@example.com>",
                to_display="me@example.com",
                subject="Hallo",
                date="",
                snippet="",
                body_text="",
            ),
        ),
    ):
        result = service.find_latest_message_by_sender("bob")
    assert result is not None
    assert result.id == "m2"
