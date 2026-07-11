"""
Test Suite für Memory Tools (Phase 5)

Test-Vorgaben aus Task M-MEM-05:
1. Write Roundtrip: write(fact="Test") → read(query="Test") | Memory found with correct priority
2. Write Guard: write(priority_override=0.99, source=skill) | priority capped to 0.95
3. Read Filter Tags: write(tags=["pet"]) → read(filter_tags=["pet"]) | Only tagged memories
4. Read Min Priority: read(min_priority=0.8) | Only high-priority memories
5. Update Happy Path: update(id=X, new_fact="Updated") | snippet changed, cache invalidated
6. Update Blocked: update(id=X) where user_editable=false | Error: "not_editable"
7. History After Update: update(id=X) → history(id=X) | change_history has 1 entry
"""

import json
from datetime import datetime

import pytest
from backend.data import contact_schemas, crud, models
from backend.data.database import Base
from backend.data.schemas_tools import ToolResultV1
from backend.services import contact_manager
from backend.services.memory.retrieval_service import get_last_subject_from_chat
from backend.tools.memory_tools import (
    _build_canonical_key,
    _parse_snippet,
    handle_memory_history,
    handle_memory_read,
    handle_memory_update,
    handle_memory_write,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _md(r: ToolResultV1) -> dict:
    return r.model_dump()


def _db_gen(db_session):
    def _factory():
        yield db_session

    return _factory


def test_get_last_subject_from_chat_skips_unknown_or_unscoped_recent_memory(db_session):
    chat_id = db_session.query(models.Chat).first().id
    anchored = models.Memory(
        chat_id=chat_id,
        snippet=json.dumps({
            "fact": "Oliver Schwab wohnt in K\u00f6ln-Stammheim",
            "subject_name": "oliver schwab",
            "subject_role": "contact",
        }),
        category="Allgemein",
        user_editable=True,
        priority=0.8,
        memory_type="GENERAL",
        change_history=[],
    )
    unknown = models.Memory(
        chat_id=chat_id,
        snippet=json.dumps({
            "fact": "Die genannte Person hat einen Hund",
            "subject_name": "unbekannt",
            "subject_role": "contact",
        }),
        category="Allgemein",
        user_editable=True,
        priority=0.5,
        memory_type="GENERAL",
        change_history=[],
    )
    db_session.add(anchored)
    db_session.commit()
    db_session.add(unknown)
    db_session.commit()

    assert get_last_subject_from_chat(db_session, chat_id) == {
        "subject_name": "oliver schwab",
        "subject_role": "contact",
    }


# Test-Datenbank Setup
@pytest.fixture(scope="function")
def db_session():
    """Erstellt eine frische SQLite In-Memory DB für jeden Test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Erstelle einen Test-Chat
    chat = models.Chat(title="Test Chat")
    session.add(chat)
    session.commit()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: Write Roundtrip
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_write_roundtrip(db_session):
    """Test 1: Write → Read Roundtrip."""
    chat_id = db_session.query(models.Chat).first().id
    
    # Write
    write_result = _md(
        await handle_memory_write(
            params={"fact": "Max hat braune Haare", "category": "Physis"},
            db=db_session,
            chat_id=chat_id,
        )
    )
    
    assert write_result["status"] == "ok"
    memory_id = write_result["data"]["memory_id"]
    
    # Read
    read_result = _md(
        await handle_memory_read(
            params={"query": "Max Haare"},
            db=db_session,
            chat_id=chat_id,
        )
    )
    
    assert read_result["status"] == "ok"
    assert read_result["data"]["total_found"] >= 1
    
    # Verify memory is in results
    memory_ids = [m["memory_id"] for m in read_result["data"]["memories"]]
    assert memory_id in memory_ids


# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: Write Guard (priority cap)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_write_priority_guard_caps_at_095(db_session):
    """Test 2: priority_override=0.99 should be capped to 0.95."""
    chat_id = db_session.query(models.Chat).first().id
    
    result = _md(
        await handle_memory_write(
            params={
                "fact": "Test fact with high priority",
                "priority_override": 0.99,  # Try to set too high
            },
            db=db_session,
            chat_id=chat_id,
        )
    )
    
    assert result["status"] == "ok"
    # Priority should be capped at 0.95
    assert result["data"]["priority"] <= 0.95


# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: Read Filter Tags
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_read_filter_tags(db_session):
    """Test 3: Write with tags → Read with filter_tags."""
    chat_id = db_session.query(models.Chat).first().id
    
    # Write with tags
    await handle_memory_write(
        params={
            "fact": "Bello ist ein Golden Retriever",
            "category": "Haustier-Details",
            "tags": ["pet", "dog"],
            "subject_name": "bello"
        },
        db=db_session,
        chat_id=chat_id
    )
    
    # Write without pet tag
    await handle_memory_write(
        params={
            "fact": "Max arbeitet bei Google",
            "category": "Beruf"
        },
        db=db_session,
        chat_id=chat_id
    )
    
    # Read with pet tag filter
    result = _md(
        await handle_memory_read(
            params={"query": "Hund", "filter_tags": ["pet"]},
            db=db_session,
            chat_id=chat_id,
        )
    )
    
    assert result["status"] == "ok"
    # All results should have pet tag
    for mem in result["data"]["memories"]:
        assert "pet" in mem["tags"]


# ═══════════════════════════════════════════════════════════════════════════
# TEST 4: Read Min Priority
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_read_min_priority(db_session):
    """Test 4: Read with min_priority filter."""
    chat_id = db_session.query(models.Chat).first().id
    
    # Write low priority
    await handle_memory_write(
        params={
            "fact": "Casual preference",
            "category": "Allgemein"
        },
        db=db_session,
        chat_id=chat_id
    )
    
    # Write high priority (Name is core identity)
    await handle_memory_write(
        params={
            "fact": "Max heißt Maximilian",
            "category": "Physis",
            "subject_name": "max",
            "evidence": "Ich heiße Maximilian"
        },
        db=db_session,
        chat_id=chat_id
    )
    
    # Read with high min_priority
    result = _md(
        await handle_memory_read(
            params={"query": "Name", "min_priority": 0.8},
            db=db_session,
            chat_id=chat_id,
        )
    )
    
    assert result["status"] == "ok"
    # All results should have priority >= 0.8
    for mem in result["data"]["memories"]:
        assert mem["priority"] >= 0.8


# ═══════════════════════════════════════════════════════════════════════════
# TEST 5: Update Happy Path
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_update_happy_path(db_session):
    """Test 5: Update existing memory."""
    chat_id = db_session.query(models.Chat).first().id
    
    # First write
    write_result = _md(
        await handle_memory_write(
            params={"fact": "Alter Fakt", "category": "Allgemein"},
            db=db_session,
            chat_id=chat_id,
        )
    )
    memory_id = write_result["data"]["memory_id"]
    
    # Update
    update_result = _md(
        await handle_memory_update(
            params={"memory_id": memory_id, "new_fact": "Neuer aktualisierter Fakt"},
            db=db_session,
        )
    )
    
    assert update_result["status"] == "ok"
    assert update_result["data"]["operation"] == "updated"
    
    # Verify change
    memory = db_session.query(models.Memory).filter(models.Memory.id == memory_id).first()
    assert "Neuer aktualisierter Fakt" in memory.snippet


# ═══════════════════════════════════════════════════════════════════════════
# TEST 6: Update Blocked (user_editable=false)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_update_blocked_not_editable(db_session):
    """Test 6: Update should fail when user_editable=false."""
    chat_id = db_session.query(models.Chat).first().id
    
    # Create memory with user_editable=False
    memory = models.Memory(
        chat_id=chat_id,
        snippet=json.dumps({"fact": "System Fakt"}),
        category="System",
        user_editable=False,
        priority=0.5,
        memory_type="GENERAL",
        change_history=[]
    )
    db_session.add(memory)
    db_session.commit()
    db_session.refresh(memory)
    
    # Try to update
    result = _md(
        await handle_memory_update(
            params={"memory_id": memory.id, "new_fact": "Versuchter Update"},
            db=db_session,
        )
    )
    
    assert result["status"] == "error"
    assert result["error"]["code"] == "NOT_EDITABLE"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 7: History After Update
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_history_after_update(db_session):
    """Test 7: History should contain entry after update."""
    chat_id = db_session.query(models.Chat).first().id
    
    # Write
    write_result = _md(
        await handle_memory_write(
            params={"fact": "Original Fakt", "category": "Allgemein"},
            db=db_session,
            chat_id=chat_id,
        )
    )
    memory_id = write_result["data"]["memory_id"]
    
    # Update
    await handle_memory_update(
        params={"memory_id": memory_id, "new_fact": "Aktualisierter Fakt"},
        db=db_session
    )
    
    # Check history
    history_result = _md(
        await handle_memory_history(
            params={"memory_id": memory_id},
            db=db_session,
        )
    )
    
    assert history_result["status"] == "ok"
    assert len(history_result["data"]["history"]) == 1
    assert history_result["data"]["history"][0]["action"] == "update"


# ═══════════════════════════════════════════════════════════════════════════
# HELPER TESTS
# ═══════════════════════════════════════════════════════════════════════════

def test_build_canonical_key_with_subject():
    """Test canonical key building with subject."""
    key = _build_canonical_key("max", "hat braune haare")
    assert "max" in key
    assert "hat_braune" in key


def test_build_canonical_key_without_subject():
    """Test canonical key building without subject (uses hash)."""
    key = _build_canonical_key(None, "some fact here")
    assert len(key) == 16  # SHA256 hex truncated


def test_parse_snippet_json():
    """Test parsing JSON snippet."""
    data = _parse_snippet('{"fact": "test fact", "priority": 0.5}')
    assert data["fact"] == "test fact"
    assert data["priority"] == 0.5


def test_parse_snippet_plain():
    """Test parsing plain text snippet."""
    data = _parse_snippet("plain text fact")
    assert data["fact"] == "plain text fact"


def test_parse_snippet_empty():
    """Test parsing empty/None snippet."""
    assert _parse_snippet(None)["fact"] == ""
    assert _parse_snippet("")["fact"] == ""


# ═══════════════════════════════════════════════════════════════════════════
# ADDITIONAL EDGE CASE TESTS
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_read_include_expired(db_session):
    """Test reading with include_expired flag."""
    chat_id = db_session.query(models.Chat).first().id
    
    # Create expired memory
    expired_memory = models.Memory(
        chat_id=chat_id,
        snippet=json.dumps({"fact": "Expired fact"}),
        category="Termine",
        expires_at=datetime(2020, 1, 1),  # Past date
        priority=0.5,
        memory_type="TEMPORAL"
    )
    db_session.add(expired_memory)
    db_session.commit()
    
    # Read without include_expired
    result_no_expired = _md(
        await handle_memory_read(
            params={"query": "Expired", "include_expired": False},
            db=db_session,
            chat_id=chat_id,
        )
    )
    
    # Read with include_expired
    result_with_expired = _md(
        await handle_memory_read(
            params={"query": "Expired", "include_expired": True},
            db=db_session,
            chat_id=chat_id,
        )
    )
    
    # Without flag should find fewer or equal
    assert result_no_expired["data"]["total_found"] <= result_with_expired["data"]["total_found"]


@pytest.mark.asyncio
async def test_memory_read_pet_overview_supplements_contact_pet_details(db_session):
    contact = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
            personal_details=[
                "hat einen Hund namens tasso",
                "hat eine Katze namens garfield",
                "Hund Tasso ist ein podenco",
                "Hund Tasso frisst gerne thunfisch",
                "Katze Garfield mag Thunfisch \u00fcberhaupt nicht",
            ],
        ),
    )
    assert contact is not None

    chat_id = db_session.query(models.Chat).first().id
    write_result = _md(
        await handle_memory_write(
            params={
                "fact": "Oli hat einen Hund namens Tasso.",
                "category": "Haustier-Details",
                "subject_name": "Oli",
                "tags": ["pet"],
            },
            db=db_session,
            chat_id=chat_id,
        )
    )
    assert write_result["status"] == "ok"

    stale_write_result = _md(
        await handle_memory_write(
            params={
                "fact": "Aber Garfield mag gar keinen Thunfisch.",
                "category": "Haustier-Details",
                "subject_name": "Oli",
                "tags": ["pet", "preference"],
            },
            db=db_session,
            chat_id=chat_id,
        )
    )
    assert stale_write_result["status"] == "ok"

    result = _md(
        await handle_memory_read(
            params={"query": "was weißt du über olis haustiere?", "limit": 10},
            db=db_session,
            chat_id=chat_id,
        )
    )
    result = _md(
        await handle_memory_read(
            params={"query": "was wei?t du ?ber olis haustiere?", "limit": 10},
            db=db_session,
            chat_id=chat_id,
        )
    )

    facts = [mem["fact"] for mem in result["data"]["memories"]]
    assert any("Oliver Schwab hat einen Hund namens tasso" in fact for fact in facts)
    assert any("Oliver Schwab hat eine Katze namens garfield" in fact for fact in facts)
    assert any("Hund Tasso ist ein podenco" in fact for fact in facts)
    assert any("Hund Tasso frisst gerne thunfisch" in fact for fact in facts)
    assert any("Katze Garfield mag Thunfisch \u00fcberhaupt nicht" in fact for fact in facts)
    assert not any("gar keinen Thunfisch" in fact for fact in facts)
    assert all(str(mem["memory_id"]).startswith("contact-") for mem in result["data"]["memories"])


@pytest.mark.asyncio
async def test_memory_read_pet_overview_recovers_missing_pet_detail_from_live_style_contact_state(db_session):
    contact = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
            personal_details=[
                "hat einen Hund namens tasso",
                "hat eine Katze namens garfield",
                "Hund Tasso ist ein podenco",
                "Hund Tasso frisst gerne thunfisch",
            ],
        ),
    )
    assert contact is not None

    chat_id = db_session.query(models.Chat).first().id
    write_result = _md(
        await handle_memory_write(
            params={
                "fact": "Garfield mag Thunfisch überhaupt nicht",
                "subject_name": "Garfield",
                "category": "Haustier-Details",
            },
            db=db_session,
            chat_id=chat_id,
            original_user_text="garfield mag thunfisch überhaupt nicht",
        )
    )
    assert write_result["status"] == "ok"

    db_contact = db_session.query(models.Contact).filter(models.Contact.id == contact.id).first()
    assert db_contact is not None
    db_contact.preferences = ["thunfisch überhaupt nicht"]
    db_contact.personal_details = [
        "hat einen Hund namens tasso",
        "hat eine Katze namens garfield",
        "Hund Tasso ist ein podenco",
        "Hund Tasso frisst gerne thunfisch",
    ]
    db_session.commit()

    result = _md(
        await handle_memory_read(
            params={"query": "was weißt du über olis haustiere?", "limit": 10},
            db=db_session,
            chat_id=chat_id,
        )
    )

    facts = [mem["fact"] for mem in result["data"]["memories"]]
    assert any("Oliver Schwab hat einen Hund namens tasso" in fact for fact in facts)
    assert any("Oliver Schwab hat eine Katze namens garfield" in fact for fact in facts)
    assert any("Hund Tasso ist ein podenco" in fact for fact in facts)
    assert any("Hund Tasso frisst gerne thunfisch" in fact for fact in facts)
    assert any("Katze Garfield mag Thunfisch überhaupt nicht" in fact for fact in facts)
    assert not any(fact.strip().casefold() == "thunfisch überhaupt nicht" for fact in facts)
    assert all(str(mem["memory_id"]).startswith("contact-") for mem in result["data"]["memories"])


@pytest.mark.asyncio
async def test_memory_write_relationship_name_fact_applies_to_existing_contact_card(db_session):
    contact = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Nathan Raimann",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert contact is not None

    chat_id = db_session.query(models.Chat).first().id
    result = _md(
        await handle_memory_write(
            params={
                "fact": "Nathans Freundin heisst Elena.",
                "subject_name": "Nathan",
                "category": "Beziehungen",
                "evidence": "nathans freundin heisst elena",
            },
            db=db_session,
            chat_id=chat_id,
            original_user_text="nathans freundin heisst elena",
        )
    )

    refreshed = crud.get_contact(db_session, contact.id)
    synced_facts = [
        _parse_snippet(memory.snippet).get("fact", "")
        for memory in db_session.query(models.Memory).all()
        if str(memory.source_type or "") == "contact_sync"
    ]

    assert result["status"] == "ok"
    assert result["data"]["contact_proposal"]["status"] == "applied"
    assert refreshed is not None
    assert refreshed.personal_details == ["Freundin heisst Elena"]
    assert any("freundin heisst elena" in fact.casefold() for fact in synced_facts)


@pytest.mark.asyncio
async def test_memory_write_relationship_named_owner_fact_applies_to_existing_contact_card(db_session):
    contact = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Nathan Raimann",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert contact is not None

    chat_id = db_session.query(models.Chat).first().id
    result = _md(
        await handle_memory_write(
            params={
                "fact": "Nathan hat eine Freundin namens Elena.",
                "subject_name": "Nathan",
                "category": "Beziehungen",
                "evidence": "nathan hat eine freundin namens elena",
            },
            db=db_session,
            chat_id=chat_id,
            original_user_text="nathan hat eine freundin namens elena",
        )
    )

    refreshed = crud.get_contact(db_session, contact.id)
    synced_facts = [
        _parse_snippet(memory.snippet).get("fact", "")
        for memory in db_session.query(models.Memory).all()
        if str(memory.source_type or "") == "contact_sync"
    ]

    assert result["status"] == "ok"
    assert result["data"]["contact_proposal"]["status"] == "applied"
    assert refreshed is not None
    assert refreshed.personal_details == ["Freundin heisst Elena"]
    assert any("freundin heisst elena" in fact.casefold() for fact in synced_facts)


@pytest.mark.asyncio
async def test_memory_not_found(db_session):
    """Test operations on non-existent memory."""
    # Update non-existent
    update_result = _md(
        await handle_memory_update(
            params={"memory_id": 99999, "new_fact": "Test"},
            db=db_session,
        )
    )
    assert update_result["status"] == "error"
    assert update_result["error"]["code"] == "NOT_FOUND"
    
    # History non-existent
    history_result = _md(
        await handle_memory_history(
            params={"memory_id": 99999},
            db=db_session,
        )
    )
    assert history_result["status"] == "error"
    assert history_result["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_update_preserves_priority_guard(db_session):
    """Test that update applies priority guard."""
    chat_id = db_session.query(models.Chat).first().id
    
    # Write
    write_result = _md(
        await handle_memory_write(
            params={"fact": "Test fact", "category": "Allgemein"},
            db=db_session,
            chat_id=chat_id,
        )
    )
    memory_id = write_result["data"]["memory_id"]
    
    # Update with very high priority (should be capped)
    update_result = _md(
        await handle_memory_update(
            params={"memory_id": memory_id, "new_fact": "Updated", "new_priority": 1.0},
            db=db_session,
        )
    )
    
    assert update_result["status"] == "ok"
    
    # Verify priority was capped
    memory = db_session.query(models.Memory).filter(models.Memory.id == memory_id).first()
    assert memory.priority <= 0.95


@pytest.mark.asyncio
async def test_write_with_ttl(db_session):
    """Test writing with TTL days."""
    chat_id = db_session.query(models.Chat).first().id
    
    result = _md(
        await handle_memory_write(
            params={
                "fact": "Temporary fact",
                "ttl_days": 30,
            },
            db=db_session,
            chat_id=chat_id,
        )
    )
    
    assert result["status"] == "ok"
    
    # Verify expires_at is set
    memory = db_session.query(models.Memory).filter(
        models.Memory.id == result["data"]["memory_id"]
    ).first()
    assert memory.expires_at is not None


@pytest.mark.asyncio
async def test_untrusted_memory_write_stages_contact_update_suggestion(db_session):
    chat_id = db_session.query(models.Chat).first().id
    contact = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Anna Erinnerung",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert contact is not None

    result = _md(
        await handle_memory_write(
            params={
                "fact": "Anna Erinnerung mag Espresso",
                "subject_name": "Anna Erinnerung",
                "category": "Vorlieben",
            },
            db=db_session,
            chat_id=chat_id,
        )
    )

    proposals = crud.list_contact_proposals(db_session, contact_id=contact.id)
    refreshed = crud.get_contact(db_session, contact.id)

    assert result["status"] == "ok"
    assert result["data"]["contact_proposal"]["proposals_staged"] == 1
    assert len(proposals) == 1
    assert proposals[0]["proposal_type"] == "memory_contact_update"
    assert proposals[0]["payload_json"]["payload"]["preferences"] == ["espresso"]
    assert refreshed.proposal_status == "pending"
    assert refreshed.proposal_source_context == "memory_sync"


@pytest.mark.asyncio
async def test_user_confirmed_memory_write_auto_applies_safe_contact_fact(db_session):
    chat_id = db_session.query(models.Chat).first().id
    contact = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Anna Erinnerung",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert contact is not None

    result = _md(
        await handle_memory_write(
            params={
                "fact": "Anna Erinnerung mag Espresso",
                "subject_name": "Anna Erinnerung",
                "category": "Vorlieben",
            },
            db=db_session,
            chat_id=chat_id,
            original_user_text="Anna Erinnerung mag Espresso",
        )
    )

    proposals = crud.list_contact_proposals(db_session, contact_id=contact.id)
    refreshed = crud.get_contact(db_session, contact.id)

    assert result["status"] == "ok"
    assert result["data"]["contact_proposal"]["status"] == "applied"
    assert result["data"]["contact_proposal"]["proposals_staged"] == 0
    assert refreshed is not None
    assert refreshed.preferences == ["espresso"]
    assert refreshed.proposal_status == "confirmed"
    assert refreshed.proposal_source_context == "direct_context"
    assert proposals == []


@pytest.mark.asyncio
async def test_user_confirmed_memory_write_stores_dietary_fact_under_personal_details(db_session):
    chat_id = db_session.query(models.Chat).first().id
    contact = models.Contact(
        name="Chris Gier",
        category="Privat",
        contact_type="private_person",
        preferences=["vegetarier", "star wars"],
        personal_details=[],
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    result = _md(
        await handle_memory_write(
            params={
                "fact": "Chris Gier ist Vegetarier",
                "subject_name": "Chris Gier",
                "category": "Vorlieben",
            },
            db=db_session,
            chat_id=chat_id,
            original_user_text="Chris ist Vegetarier",
        )
    )

    refreshed = crud.get_contact(db_session, contact.id)

    assert result["status"] == "ok"
    assert result["data"]["contact_proposal"]["status"] == "applied"
    assert refreshed is not None
    assert refreshed.preferences == ["star wars"]
    assert refreshed.personal_details == ["vegetarier"]


@pytest.mark.asyncio
async def test_memory_write_rebinds_explicit_lead_contact_subject_from_original_user_text(db_session):
    chat_id = db_session.query(models.Chat).first().id
    crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
        ),
    )

    result = _md(
        await handle_memory_write(
            params={
                "fact": "Oli liebt Big Bang Theory.",
                "category": "Vorlieben",
            },
            db=db_session,
            chat_id=chat_id,
            original_user_text="Olix liebt Big Bang Theory",
        )
    )

    memory_id = result["data"]["memory_id"]
    saved = db_session.query(models.Memory).filter(models.Memory.id == memory_id).first()
    parsed = contact_manager._parse_memory_snippet_payload(saved.snippet)

    assert result["status"] == "ok"
    assert parsed["subject_name"] == "Olix"
    assert parsed["fact"].startswith("Olix liebt")
    assert "olix" in str(saved.canonical_key).lower()


@pytest.mark.asyncio
async def test_memory_read_filters_contact_recall_to_matching_subject(db_session):
    chat_id = db_session.query(models.Chat).first().id
    oli = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
        ),
    )
    chris = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Chris Gier",
            nickname="Cris",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert oli is not None
    assert chris is not None

    await handle_memory_write(
        params={
            "fact": "Oli liebt Big Bang Theory",
            "subject_name": "Oli",
            "category": "Vorlieben",
        },
        db=db_session,
        chat_id=chat_id,
        original_user_text="Oli liebt Big Bang Theory",
    )
    await handle_memory_write(
        params={
            "fact": "Chris Gier liebt Kimchi",
            "subject_name": "Chris Gier",
            "category": "Vorlieben",
        },
        db=db_session,
        chat_id=chat_id,
        original_user_text="Chris Gier liebt Kimchi",
    )

    result = _md(
        await handle_memory_read(
            params={"query": "Oli Vorlieben Hobbys Interessen", "limit": 10},
            db=db_session,
            chat_id=chat_id,
        )
    )

    facts = [mem["fact"] for mem in result["data"]["memories"]]

    assert result["status"] == "ok"
    assert any(fact.casefold() == "oli liebt big bang theory" for fact in facts)
    assert all("chris gier" not in fact.casefold() for fact in facts)


@pytest.mark.asyncio
async def test_memory_read_filters_relationship_recall_to_matching_possessive_subject(db_session):
    chat_id = db_session.query(models.Chat).first().id
    crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Timo Testmann",
            nickname="Timo",
            category="Privat",
            contact_type="private_person",
        ),
    )
    crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Nathan Raimann",
            nickname="Nathan",
            category="Privat",
            contact_type="private_person",
        ),
    )

    await handle_memory_write(
        params={
            "fact": "Timos Freundin heisst Mira.",
            "subject_name": "Timo",
            "category": "Beziehungen",
        },
        db=db_session,
        chat_id=chat_id,
        original_user_text="timos freundin heisst mira",
    )
    await handle_memory_write(
        params={
            "fact": "Nathans Freundin heisst Elena.",
            "subject_name": "Nathan",
            "category": "Beziehungen",
        },
        db=db_session,
        chat_id=chat_id,
        original_user_text="nathans freundin heisst elena",
    )

    result = _md(
        await handle_memory_read(
            params={"query": "wer ist timos freundin?", "limit": 10},
            db=db_session,
            chat_id=chat_id,
        )
    )

    facts = [mem["fact"].casefold() for mem in result["data"]["memories"]]

    assert result["status"] == "ok"
    assert any("timo" in fact and "mira" in fact for fact in facts)
    assert all("nathan" not in fact for fact in facts)


@pytest.mark.asyncio
async def test_memory_read_filters_contact_recall_for_unknown_subject_alias_without_address_book_match(
    db_session,
):
    chat_id = db_session.query(models.Chat).first().id
    contact = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert contact is not None

    await handle_memory_write(
        params={
            "fact": "Oli liebt Kimchi",
            "subject_name": "Oli",
            "category": "Vorlieben",
        },
        db=db_session,
        chat_id=chat_id,
        original_user_text="Oli liebt Kimchi",
    )
    await handle_memory_write(
        params={
            "fact": "Olix Quarz liebt Big Bang Theory",
            "subject_name": "Olix Quarz",
            "category": "Vorlieben",
        },
        db=db_session,
        chat_id=chat_id,
        original_user_text="Olix Quarz liebt Big Bang Theory",
    )

    result = _md(
        await handle_memory_read(
            params={"query": "was mag olix?", "limit": 10},
            db=db_session,
            chat_id=chat_id,
        )
    )

    facts = [mem["fact"] for mem in result["data"]["memories"]]

    assert result["status"] == "ok"
    assert any("olix quarz" in fact.casefold() for fact in facts)
    assert all("oli liebt kimchi" != fact.casefold() for fact in facts)


@pytest.mark.asyncio
async def test_memory_read_keeps_both_subjects_for_multi_contact_query(db_session):
    chat_id = db_session.query(models.Chat).first().id
    crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Chris Gier",
            nickname="Chris",
            category="Privat",
            contact_type="private_person",
        ),
    )
    crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
        ),
    )

    await handle_memory_write(
        params={
            "fact": "Chris Gier liebt Kimchi",
            "subject_name": "Chris Gier",
            "category": "Vorlieben",
        },
        db=db_session,
        chat_id=chat_id,
        original_user_text="Chris Gier liebt Kimchi",
    )
    await handle_memory_write(
        params={
            "fact": "Oli liebt Big Bang Theory",
            "subject_name": "Oli",
            "category": "Vorlieben",
        },
        db=db_session,
        chat_id=chat_id,
        original_user_text="Oli liebt Big Bang Theory",
    )
    await handle_memory_write(
        params={
            "fact": "Petra liebt Espresso",
            "subject_name": "Petra",
            "category": "Vorlieben",
        },
        db=db_session,
        chat_id=chat_id,
        original_user_text="Petra liebt Espresso",
    )

    result = _md(
        await handle_memory_read(
            params={"query": "was mögen chris und oli?", "limit": 10},
            db=db_session,
            chat_id=chat_id,
        )
    )

    facts = [mem["fact"].casefold() for mem in result["data"]["memories"]]

    assert result["status"] == "ok"
    assert any("chris gier liebt kimchi" == fact for fact in facts)
    assert any("oli liebt big bang theory" == fact for fact in facts)
    assert all("petra liebt espresso" != fact for fact in facts)


@pytest.mark.asyncio
async def test_memory_read_prefers_primary_subject_frame_over_later_alias_noise(db_session):
    chat_id = db_session.query(models.Chat).first().id
    contact = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert contact is not None

    await handle_memory_write(
        params={
            "fact": "Oli liebt Kimchi",
            "subject_name": "Oli",
            "category": "Vorlieben",
        },
        db=db_session,
        chat_id=chat_id,
        original_user_text="Oli liebt Kimchi",
    )
    await handle_memory_write(
        params={
            "fact": "Olix Quarz liebt Big Bang Theory",
            "subject_name": "Olix Quarz",
            "category": "Vorlieben",
        },
        db=db_session,
        chat_id=chat_id,
        original_user_text="Olix Quarz liebt Big Bang Theory",
    )

    result = _md(
        await handle_memory_read(
            params={"query": "Was mag Olix? Vorlieben von Olix Oli", "limit": 25},
            db=db_session,
            chat_id=chat_id,
        )
    )

    facts = [mem["fact"] for mem in result["data"]["memories"]]

    assert result["status"] == "ok"
    assert any("olix quarz" in fact.casefold() for fact in facts)
    assert all("oli liebt kimchi" != fact.casefold() for fact in facts)

    variant = _md(
        await handle_memory_read(
            params={"query": "Präferenzen von Olix oder Oli oder Olix Quarz", "limit": 25},
            db=db_session,
            chat_id=chat_id,
        )
    )

    variant_facts = [mem["fact"] for mem in variant["data"]["memories"]]

    assert variant["status"] == "ok"
    assert any("olix quarz" in fact.casefold() for fact in variant_facts)
    assert all("oli liebt kimchi" != fact.casefold() for fact in variant_facts)


@pytest.mark.asyncio
async def test_rejected_memory_contact_suggestion_is_suppressed_until_new_evidence(db_session):
    chat_id = db_session.query(models.Chat).first().id
    contact_manager._clear_pending_contact_proposals_for_tests()
    contact = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Anna Erinnerung",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert contact is not None

    first = _md(
        await handle_memory_write(
            params={
                "fact": "Anna Erinnerung mag Espresso",
                "subject_name": "Anna Erinnerung",
                "category": "Vorlieben",
            },
            db=db_session,
            chat_id=chat_id,
        )
    )
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "backend.services.contact_manager.database.get_db_sync",
            _db_gen(db_session),
        )
        reject_result = contact_manager.reject_pending_contact_proposal(chat_id)
    second = _md(
        await handle_memory_write(
            params={
                "fact": "Anna Erinnerung mag Espresso",
                "subject_name": "Anna Erinnerung",
                "category": "Vorlieben",
            },
            db=db_session,
            chat_id=chat_id,
        )
    )

    proposals = crud.list_contact_proposals(db_session, contact_id=contact.id)
    refreshed = crud.get_contact(db_session, contact.id)

    assert first["status"] == "ok"
    assert first["data"]["contact_proposal"]["proposals_staged"] == 1
    assert reject_result["status"] == "rejected"
    assert second["status"] == "ok"
    assert second["data"]["contact_proposal"]["proposals_staged"] == 0
    assert second["data"]["contact_proposal"]["suppressed"] == 1
    assert len(proposals) == 1
    assert proposals[0]["status"] == "rejected"
    assert refreshed.proposal_status == "confirmed"
    assert refreshed.proposal_source_context == "memory_sync"
