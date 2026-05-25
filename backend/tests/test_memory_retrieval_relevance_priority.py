import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.data import models
from backend.data.database import Base
from backend.services.memory.retrieval_service import (
    _is_context_privacy_memory_suppressed_query,
)
from backend.services.memory_budget import (
    MemorySlot,
    TokenBudget,
    extract_fact_coupons,
    format_memory_context,
    select_slots_by_budget,
)
from backend.tools.memory_tools import handle_memory_read


def _md(result):
    return result.model_dump()


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def _add_chat(db, title):
    chat = models.Chat(title=title)
    db.add(chat)
    db.commit()
    return chat


def _add_memory(db, chat_id, fact, *, priority=0.5, category="Allgemein", tags=None, canonical_key=None):
    memory = models.Memory(
        chat_id=chat_id,
        snippet=json.dumps({"fact": fact}, ensure_ascii=False),
        embedding_json=json.dumps([0.1, 0.2, 0.3]).encode("utf-8"),
        normalized_text=fact.lower(),
        text_hash=f"hash-{fact}",
        category=category,
        priority=priority,
        memory_type="CORE" if priority >= 0.8 else "GENERAL",
        tags=tags or [],
        canonical_key=canonical_key or fact.lower().replace(" ", "|"),
        source_skill="system.extractor",
        user_editable=True,
    )
    db.add(memory)
    db.commit()
    return memory


def test_high_priority_project_memory_beats_chat_title_placeholder():
    slots = [
        MemorySlot(
            text="Das Testprojekt heisst Phoenix.",
            tokens=40,
            tier="core_identity",
            priority=0.95,
            memory_id=2,
            tags=["project"],
            chat_title="Name des Testprojekts",
        ),
        MemorySlot(
            text="Chat-Titel Platzhalter: Name des Testprojekts.",
            tokens=40,
            tier="stm",
            priority=0.30,
            memory_id=1,
            tags=["title"],
            chat_title="Name des Testprojekts",
        ),
    ]

    selected = select_slots_by_budget(slots, TokenBudget(max_tokens=2000, memory_ratio=0.5))
    context = format_memory_context(selected)

    assert selected[0].text == "Das Testprojekt heisst Phoenix."
    assert "Phoenix" in context
    assert "Chat-Titel Platzhalter" not in context


def test_relevant_preferences_emit_fact_coupons_for_preference_query():
    slots = [
        MemorySlot(
            text="Der Nutzer mag vegetarische bayerische Kueche und kleine Museen.",
            tokens=30,
            tier="global_query",
            priority=0.80,
            memory_id=10,
            tags=["Vorlieben"],
        )
    ]

    coupons = extract_fact_coupons(
        slots,
        "Ich fahre nach Muenchen. Was passt zu meinen Vorlieben?",
    )

    assert coupons == [
        "[PREFERENCE] Der Nutzer mag vegetarische bayerische Kueche und kleine Museen."
    ]


def test_unrelated_geo_query_suppresses_private_memory_context():
    assert _is_context_privacy_memory_suppressed_query("Wie weit ist Koeln von Hamburg?")
    assert _is_context_privacy_memory_suppressed_query("Welche Route ist kuerzer von Koeln nach Hamburg?")


@pytest.mark.asyncio
async def test_missing_favorite_color_is_not_returned_from_unrelated_memory(db_session):
    chat = _add_chat(db_session, "Name des Testprojekts")
    _add_memory(
        db_session,
        chat.id,
        "Das Testprojekt heisst Phoenix.",
        priority=0.95,
        category="Beruf",
        tags=["project"],
    )
    _add_memory(
        db_session,
        chat.id,
        "Der Nutzer mag vegetarische bayerische Kueche.",
        priority=0.75,
        category="Vorlieben",
        tags=["Vorlieben"],
    )

    result = _md(
        await handle_memory_read(
            {"query": "Lieblingsfarbe", "limit": 5},
            db_session,
            chat.id,
        )
    )

    assert result["status"] == "ok"
    assert result["data"]["total_found"] == 0


@pytest.mark.asyncio
async def test_memory_read_returns_relevant_project_but_not_placeholder(db_session):
    chat = _add_chat(db_session, "Name des Testprojekts")
    project = _add_memory(
        db_session,
        chat.id,
        "Das Testprojekt heisst Phoenix.",
        priority=0.95,
        category="Beruf",
        tags=["project"],
        canonical_key="user|testprojekt|phoenix",
    )

    result = _md(
        await handle_memory_read(
            {"query": "Testprojekt", "limit": 5},
            db_session,
            chat.id,
        )
    )

    facts = [memory["fact"] for memory in result["data"]["memories"]]
    assert result["status"] == "ok"
    assert project.id in [memory["memory_id"] for memory in result["data"]["memories"]]
    assert any("Phoenix" in fact for fact in facts)
    assert all("Name des Testprojekts" not in fact for fact in facts)
