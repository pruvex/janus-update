import pytest
import datetime
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.data.database import Base, Memory
from backend.services import memory_manager, vector_service

# --- FIXTURES (Setup) ---

@pytest.fixture(scope="function")
def db_session():
    """Erstellt eine temporäre In-Memory SQLite Datenbank für jeden Test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Mocking Vector Service für deterministische Tests
    # Wir überschreiben die echte Vektor-Berechnung mit einer Dummy-Funktion,
    # damit wir keine echten Models laden müssen (schneller).
    original_generate = vector_service.generate_embedding
    original_find = vector_service.find_most_similar_indices
    
    # Dummy Embedding: Einfach eine Liste von Nullen
    vector_service.generate_embedding = lambda text: json.dumps([0.1] * 384)
    
    # Dummy Search: Findet immer alles (Indizes 0 bis N)
    # Wir testen die Filter-Logik des Managers, nicht die Mathe von NumPy
    vector_service.find_most_similar_indices = lambda q, e, top_k, threshold: list(range(len(e)))[:top_k]

    yield session

    # Cleanup & Restore
    session.close()
    vector_service.generate_embedding = original_generate
    vector_service.find_most_similar_indices = original_find

# --- TESTS ---

def test_core_memory_retrieval(db_session):
    """Testet, ob Core-Fakten (Prio 2) immer und global geladen werden."""
    # Arrange
    memory_manager.save_memory_snippet(db_session, chat_id=1, snippet_text="User heißt Maverick", is_core=True, core_priority=2)
    memory_manager.save_memory_snippet(db_session, chat_id=1, snippet_text="User ist Veganer", is_core=True, core_priority=2)
    memory_manager.save_memory_snippet(db_session, chat_id=1, snippet_text="User mag Pizza", is_core=True, core_priority=1) # Prio 1
    
    # Act: Abruf aus einem GANZ ANDEREN Chat (ID 99)
    context = memory_manager.retrieve_diamond_context(db_session, chat_id=99, query="Wer bin ich?")
    
    # Assert
    print(f"Context: {context}")
    assert "User heißt Maverick" in context
    assert "User ist Veganer" in context
    assert "### CORE IDENTITY" in context
    # Prio 1 sollte hier NICHT sein, da Vektor-Suche gemockt ist aber Prio 2 hardgecodet geladen wird
    # (In diesem Test-Setup prüfen wir nur den SQL-Abruf von Prio 2)

def test_ephemeral_expiry(db_session):
    """Testet, ob abgelaufene Fakten verschwinden."""
    # Arrange
    now = datetime.datetime.now()
    past = now - datetime.timedelta(hours=2) # Vor 2 Stunden abgelaufen
    future = now + datetime.timedelta(hours=2) # Läuft erst in 2 Stunden ab
    
    # Abgelaufen
    memory_manager.save_memory_snippet(
        db_session, chat_id=1, snippet_text="Alter Termin", category="Termin", expires_at=past
    )
    # Aktiv
    memory_manager.save_memory_snippet(
        db_session, chat_id=1, snippet_text="Zukünftiger Termin", category="Termin", expires_at=future
    )
    
    # Act
    context = memory_manager.retrieve_diamond_context(db_session, chat_id=1, query="Termine")
    
    # Assert
    assert "Zukünftiger Termin" in context
    assert "Alter Termin" not in context  # Darf NICHT auftauchen!

def test_ephemeral_cross_chat(db_session):
    """Testet, ob Termine global (chat-übergreifend) sichtbar sind."""
    future = datetime.datetime.now() + datetime.timedelta(hours=24)
    
    # Termin in Chat 1 gespeichert
    memory_manager.save_memory_snippet(
        db_session, chat_id=1, snippet_text="Zahnarzt morgen", category="Termin", expires_at=future
    )
    
    # Abruf in Chat 2
    context = memory_manager.retrieve_diamond_context(db_session, chat_id=2, query="Was liegt an?")
    
    # Assert
    assert "Zahnarzt morgen" in context

def test_stm_isolation(db_session):
    """Testet, ob normales STM (Short Term Memory) strikt lokal bleibt."""
    # Chat 1 redet über Autos
    memory_manager.save_memory_snippet(db_session, chat_id=1, snippet_text="Rotes Auto", is_core=False)
    
    # Chat 2 redet über Blumen
    memory_manager.save_memory_snippet(db_session, chat_id=2, snippet_text="Blaue Blume", is_core=False)
    
    # Abruf in Chat 2
    context = memory_manager.retrieve_diamond_context(db_session, chat_id=2, query="Zusammenfassung")
    
    # Assert
    assert "Blaue Blume" in context
    assert "Rotes Auto" not in context # Darf NICHT leaken!

def test_grace_period_echo(db_session):
    """Testet, ob 'Echo Memory' (Grace Period) funktioniert bei Vergangenheitsfragen."""
    now = datetime.datetime.now()
    expired_but_retained = now - datetime.timedelta(hours=1)
    
    # Speichern mit expires_at in der Vergangenheit, aber retain_until (automatisch +7 Tage) in der Zukunft
    memory_manager.save_memory_snippet(
        db_session, chat_id=1, snippet_text="Gestriger Kinofilm", category="Event", expires_at=expired_but_retained
    )
    
    # 1. Normale Frage ("Was ist los?") -> Sollte leer sein
    context_normal = memory_manager.retrieve_diamond_context(db_session, chat_id=1, query="Was steht an?")
    assert "Gestriger Kinofilm" not in context_normal
    
    # 2. Vergangenheitsfrage ("Was war gestern?") -> Sollte gefunden werden (Echo)
    context_past = memory_manager.retrieve_diamond_context(db_session, chat_id=1, query="Was war gestern im Kino?")
    assert "Gestriger Kinofilm" in context_past
    assert "RECENTLY EXPIRED" in context_past
