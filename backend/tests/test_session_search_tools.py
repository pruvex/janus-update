import importlib
from datetime import datetime, timezone

from backend.data import crud, models
from backend.services.memory.session_fts_store import SessionFTSStore
from backend.tools.session_search_tools import handle_session_search


def test_create_message_indexes_into_session_search_when_enabled(db_session, monkeypatch, tmp_path):
    service = importlib.import_module("backend.services.memory.session_search_service")
    monkeypatch.setattr(service, "MEMORY_SESSION_SEARCH_ENABLED", True)

    db_path = tmp_path / "session_fts.db"
    monkeypatch.setattr("backend.services.memory.session_fts_store.SESSION_FTS_DB_PATH", str(db_path))

    chat = models.Chat(title="Session Search")
    db_session.add(chat)
    db_session.commit()

    message = crud.create_message(db_session, chat.id, "user", "Die Firma heisst Acme GmbH.")

    with SessionFTSStore(db_path=str(db_path)) as store:
        matches = store.search(query="Acme", limit=5)

    assert message.id is not None
    assert len(matches) == 1
    assert matches[0].message_id == message.id


def test_handle_session_search_filters_sensitive_results(db_session, monkeypatch, tmp_path):
    service = importlib.import_module("backend.services.memory.session_search_service")
    monkeypatch.setattr(service, "MEMORY_SESSION_SEARCH_ENABLED", True)

    db_path = tmp_path / "session_fts.db"
    with SessionFTSStore(db_path=str(db_path)) as store:
        store.index_message(
            message_id=1,
            chat_id=1,
            role="user",
            content="Die Firma heisst Acme GmbH.",
            created_at=datetime.now(timezone.utc),
        )
        store.index_message(
            message_id=2,
            chat_id=1,
            role="user",
            content="mein passwort ist SECRET-12345",
            created_at=datetime.now(timezone.utc),
        )

    result = __import__("asyncio").run(
        handle_session_search({"query": "Acme", "limit": 5}, db_session, db_path=str(db_path))
    )
    payload = result.model_dump()

    assert payload["status"] == "ok"
    assert payload["data"]["total_found"] == 1
    assert payload["data"]["matches"][0]["chat_id"] == 1
    assert "Acme" in payload["data"]["matches"][0]["snippet"]


def test_handle_session_search_filters_plain_password_like_results(db_session, monkeypatch, tmp_path):
    service = importlib.import_module("backend.services.memory.session_search_service")
    monkeypatch.setattr(service, "MEMORY_SESSION_SEARCH_ENABLED", True)

    db_path = tmp_path / "session_fts.db"
    with SessionFTSStore(db_path=str(db_path)) as store:
        store.index_message(
            message_id=1,
            chat_id=1,
            role="user",
            content="mein passwort ist geheim123",
            created_at=datetime.now(timezone.utc),
        )

    result = __import__("asyncio").run(
        handle_session_search({"query": "geheim123", "limit": 5}, db_session, db_path=str(db_path))
    )
    payload = result.model_dump()

    assert payload["status"] == "ok"
    assert payload["data"]["total_found"] == 0


def test_handle_session_search_accepts_natural_language_question_queries(db_session, monkeypatch, tmp_path):
    service = importlib.import_module("backend.services.memory.session_search_service")
    monkeypatch.setattr(service, "MEMORY_SESSION_SEARCH_ENABLED", True)

    db_path = tmp_path / "session_fts.db"
    with SessionFTSStore(db_path=str(db_path)) as store:
        store.index_message(
            message_id=1,
            chat_id=1,
            role="user",
            content="Die Firma heisst Acme GmbH.",
            created_at=datetime.now(timezone.utc),
        )

    result = __import__("asyncio").run(
        handle_session_search({"query": "Wie hiess die Firma?", "limit": 5}, db_session, db_path=str(db_path))
    )
    payload = result.model_dump()

    assert payload["status"] == "ok"
    assert payload["data"]["total_found"] == 1
    assert payload["data"]["matches"][0]["message_id"] == 1


def test_handle_session_search_skips_question_echo_rows_for_recall_queries(db_session, monkeypatch, tmp_path):
    service = importlib.import_module("backend.services.memory.session_search_service")
    monkeypatch.setattr(service, "MEMORY_SESSION_SEARCH_ENABLED", True)

    db_path = tmp_path / "session_fts.db"
    with SessionFTSStore(db_path=str(db_path)) as store:
        store.index_message(
            message_id=1,
            chat_id=1,
            role="user",
            content="Wie hiess die Firma?",
            created_at=datetime.now(timezone.utc),
        )
        store.index_message(
            message_id=2,
            chat_id=2,
            role="user",
            content="Wie hiess die Firma?",
            created_at=datetime.now(timezone.utc),
        )
        store.index_message(
            message_id=3,
            chat_id=3,
            role="user",
            content="Die Firma heisst Acme GmbH und wir wollen das spaeter wiederfinden.",
            created_at=datetime.now(timezone.utc),
        )

    result = __import__("asyncio").run(
        handle_session_search({"query": "Wie hiess die Firma?", "limit": 5}, db_session, db_path=str(db_path))
    )
    payload = result.model_dump()

    assert payload["status"] == "ok"
    assert payload["data"]["total_found"] == 1
    assert payload["data"]["matches"][0]["message_id"] == 3
    assert "Acme GmbH" in payload["data"]["matches"][0]["content_preview"]
