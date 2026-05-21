import importlib
import logging

from backend.logger_config import SensitiveRedactionFilter
from backend.utils.redaction import REDACTION_TEXT, redact_sensitive_text, redact_sensitive_value


def test_redacts_common_secret_shapes():
    raw = (
        "Authorization: Bearer abcdefghijklmnop\n"
        "Cookie: sessionid=supersecret\n"
        "api_key=JANUS_FAKE_GOOGLE_KEY_REDACTION_TEST\n"
        "secret=SECRET-OBSERVABILITY-123"
    )

    redacted = redact_sensitive_text(raw)

    assert "abcdefghijklmnop" not in redacted
    assert "sessionid=supersecret" not in redacted
    assert "JANUS_FAKE_GOOGLE_KEY_REDACTION_TEST" not in redacted
    assert "SECRET-OBSERVABILITY-123" not in redacted
    assert REDACTION_TEXT in redacted


def test_redacts_sensitive_mapping_keys_recursively():
    raw = {
        "provider": "openai",
        "authorization": "Bearer abcdefghijklmnop",
        "nested": {
            "client_secret": "SECRET-OBSERVABILITY-123",
            "status": "ok",
            "prompt": "JANUS_PRIVATE_PROMPT_CANARY_20260521",
            "content": "JANUS_PRIVATE_FILE_CONTENT_CANARY_20260521",
        },
    }

    redacted = redact_sensitive_value(raw)

    assert redacted["provider"] == "openai"
    assert redacted["authorization"] == REDACTION_TEXT
    assert redacted["nested"]["client_secret"] == REDACTION_TEXT
    assert redacted["nested"]["status"] == "ok"
    assert redacted["nested"]["prompt"] == REDACTION_TEXT
    assert redacted["nested"]["content"] == REDACTION_TEXT


def test_logging_filter_redacts_message_and_args():
    record = logging.LogRecord(
        "janus_backend",
        logging.INFO,
        __file__,
        1,
        "token=%s payload=%s",
        ("SECRET-OBSERVABILITY-123", {"authorization": "Bearer abcdefghijklmnop"}),
        None,
    )

    assert SensitiveRedactionFilter().filter(record)
    rendered = record.getMessage()

    assert "SECRET-OBSERVABILITY-123" not in rendered
    assert "abcdefghijklmnop" not in rendered
    assert REDACTION_TEXT in rendered


def test_logging_filter_redacts_binary_header_tuples():
    record = logging.LogRecord(
        "hpack.hpack",
        logging.DEBUG,
        __file__,
        1,
        "Adding %r to the header table, sensitive:%s",
        ((b"apikey", b"sb_publishable_FAKE_REDACTION_TEST_TOKEN_DO_NOT_USE"), False),
        None,
    )

    assert SensitiveRedactionFilter().filter(record)
    rendered = record.getMessage()

    assert "sb_publishable_FAKE_REDACTION_TEST_TOKEN_DO_NOT_USE" not in rendered
    assert REDACTION_TEXT in rendered


def test_telemetry_has_no_default_webhook_and_sanitizes_logs(tmp_path, monkeypatch):
    monkeypatch.delenv("FEEDBACK_WEBHOOK_URL", raising=False)
    telemetry = importlib.import_module("backend.services.telemetry_service")
    telemetry = importlib.reload(telemetry)

    assert telemetry.FEEDBACK_WEBHOOK_URL == ""

    log_file = tmp_path / "janus_backend.log"
    log_file.write_text("Authorization: Bearer abcdefghijklmnop\n", encoding="utf-8")
    monkeypatch.setattr(telemetry, "LOG_FILE_PATH", str(log_file))

    content = telemetry._read_last_log_lines(10)

    assert "abcdefghijklmnop" not in content
    assert REDACTION_TEXT in content
