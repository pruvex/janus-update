import json
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.data import models
from backend.data.database import Base
from backend.services.memory.retrieval_service import retrieve_diamond_slots, should_inject_memory


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def _add_chat(db, title: str) -> models.Chat:
    chat = models.Chat(title=title)
    db.add(chat)
    db.commit()
    return chat


def _add_memory(db, chat_id: int, fact: str, *, category: str, priority: float, tags=None) -> models.Memory:
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
        canonical_key=fact.lower().replace(" ", "|"),
        source_skill="system.extractor",
        user_editable=True,
    )
    db.add(memory)
    db.commit()
    return memory


def test_should_inject_memory_allows_weather_query_with_personal_scope_hint():
    intent = SimpleNamespace(
        is_personal_recall=False,
        is_fact_telling=False,
        is_self_referential=False,
        is_calendar_intent=False,
        is_weather_intent=True,
        is_routing_geo_intent=False,
        is_wikipedia_intent=False,
        is_news_intent=False,
        is_local_business_intent=False,
        is_shopping_intent=False,
    )

    assert should_inject_memory("Wie wird das Wetter in Berlin, wo ich wohne?", intent) is True


def test_should_inject_memory_blocks_generic_weather_query():
    intent = SimpleNamespace(
        is_personal_recall=False,
        is_fact_telling=False,
        is_self_referential=False,
        is_calendar_intent=False,
        is_weather_intent=True,
        is_routing_geo_intent=False,
        is_wikipedia_intent=False,
        is_news_intent=False,
        is_local_business_intent=False,
        is_shopping_intent=False,
    )

    assert should_inject_memory("Wie wird das Wetter morgen?", intent) is False


def test_retrieve_diamond_slots_health_only_mode_does_not_require_query_embedding(db_session, monkeypatch):
    chat = _add_chat(db_session, "Health Safety")
    _add_memory(
        db_session,
        chat.id,
        "Der Nutzer hat eine schwere Nussallergie.",
        category="Gesundheit",
        priority=0.4,
        tags=["medical"],
    )
    _add_memory(
        db_session,
        chat.id,
        "Der Nutzer mag Science-Fiction.",
        category="Vorlieben",
        priority=0.7,
        tags=["preference"],
    )

    monkeypatch.setattr(
        "backend.services.memory.retrieval_service.vector_service.get_query_embedding",
        lambda _query: (_ for _ in ()).throw(AssertionError("query embedding should not run in health-only mode")),
    )

    slots = retrieve_diamond_slots(
        db_session,
        chat.id,
        "Wie wird das Wetter morgen?",
        include_general_memory=False,
    )

    assert len(slots) == 1
    assert "Nussallergie" in slots[0].text
    assert slots[0].tier == "health_mandatory"
