from datetime import datetime, timezone

from backend.services.memory.session_fts_store import SessionFTSStore


def test_session_fts_store_indexes_and_searches_messages(tmp_path):
    db_path = tmp_path / "session_fts.db"
    with SessionFTSStore(db_path=str(db_path)) as store:
        store.index_message(
            message_id=1,
            chat_id=10,
            role="user",
            content="Die Firma heisst Acme GmbH und sitzt in Berlin.",
            created_at=datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc),
        )
        store.index_message(
            message_id=2,
            chat_id=11,
            role="user",
            content="Oli mochte das Angebot von Acme nicht.",
            created_at=datetime(2026, 7, 11, 12, 0, tzinfo=timezone.utc),
        )

        results = store.search(query="Acme", limit=5)

    assert len(results) == 2
    assert results[0].message_id in {1, 2}
    assert all("Acme" in row.content for row in results)


def test_session_fts_store_filters_by_chat_and_since_days(tmp_path):
    db_path = tmp_path / "session_fts.db"
    with SessionFTSStore(db_path=str(db_path)) as store:
        store.index_message(
            message_id=1,
            chat_id=10,
            role="user",
            content="Wir haben ueber Acme gesprochen.",
            created_at=datetime.now(timezone.utc),
        )
        store.index_message(
            message_id=2,
            chat_id=11,
            role="user",
            content="Acme kam auch im anderen Chat vor.",
            created_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )

        filtered = store.search(query="Acme", chat_id=10, since_days=30, limit=5)

    assert len(filtered) == 1
    assert filtered[0].chat_id == 10


def test_session_fts_store_handles_natural_language_question_queries(tmp_path):
    db_path = tmp_path / "session_fts.db"
    with SessionFTSStore(db_path=str(db_path)) as store:
        store.index_message(
            message_id=1,
            chat_id=10,
            role="user",
            content="Die Firma heisst Acme GmbH und sitzt in Berlin.",
            created_at=datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc),
        )

        results = store.search(query="Wie hiess die Firma?", limit=5)

    assert len(results) == 1
    assert results[0].message_id == 1


def test_session_fts_store_collects_fallback_candidates_beyond_question_echo_rows(tmp_path):
    db_path = tmp_path / "session_fts.db"
    with SessionFTSStore(db_path=str(db_path)) as store:
        store.index_message(
            message_id=1,
            chat_id=10,
            role="user",
            content="Wie hiess die Firma?",
            created_at=datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc),
        )
        store.index_message(
            message_id=2,
            chat_id=11,
            role="user",
            content="Die Firma heisst Acme GmbH und sitzt in Berlin.",
            created_at=datetime(2026, 7, 10, 12, 5, tzinfo=timezone.utc),
        )

        results = store.search(query="Wie hiess die Firma?", limit=5)

    assert [row.message_id for row in results] == [1, 2]
