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
from backend.data import models
from backend.data.database import Base
from backend.data.schemas_tools import ToolResultV1
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
