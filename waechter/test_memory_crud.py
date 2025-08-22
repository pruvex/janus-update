import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base, Chat, Memory # Memory importieren
from backend import crud

# Eine separate In-Memory-Datenbank für Tests verwenden
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Pytest Fixture, um eine saubere DB-Sitzung für jeden Test bereitzustellen
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Erstelle einen Dummy-Chat, da Memory einen Foreign Key zu Chat hat
    dummy_chat = Chat(title="Dummy Chat for Memory")
    db.add(dummy_chat)
    db.commit()
    db.refresh(dummy_chat)
    db.dummy_chat_id = dummy_chat.id
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_save_memory_snippet(db_session):
    """Testet, ob ein neuer Memory-Snippet korrekt gespeichert wird."""
    snippet_text = "Der Benutzer heißt Klaus."
        
    saved_memory = crud.save_memory_snippet(db_session, chat_id=db_session.dummy_chat_id, snippet_text=snippet_text)
        
    assert saved_memory is not None
    assert saved_memory.id is not None
    assert saved_memory.snippet == snippet_text
    assert saved_memory.chat_id == db_session.dummy_chat_id

def test_search_memory_by_text(db_session):
    """Testet, ob die Textsuche in den Memory-Snippets funktioniert."""
    crud.save_memory_snippet(db_session, chat_id=db_session.dummy_chat_id, snippet_text="Der Benutzer heißt Klaus.")
    crud.save_memory_snippet(db_session, chat_id=db_session.dummy_chat_id, snippet_text="Die Lieblingsfarbe des Benutzers ist Blau.")
    crud.save_memory_snippet(db_session, chat_id=db_session.dummy_chat_id, snippet_text="Das Projekt heißt Janus.")
    # Testfall 1: Suche nach einem exakten Wort
    search_results_klaus = crud.search_memory_by_text(db_session, search_term="Klaus")
    assert len(search_results_klaus) == 1
    assert search_results_klaus[0].snippet == "Der Benutzer heißt Klaus."
    # Testfall 2: Suche nach einem Teilwort
    search_results_farbe = crud.search_memory_by_text(db_session, search_term="farbe")
    assert len(search_results_farbe) == 1
    assert "Blau" in search_results_farbe[0].snippet
    # Testfall 3: Suche nach etwas, das nicht existiert
    search_results_none = crud.search_memory_by_text(db_session, search_term="Berlin")
    assert len(search_results_none) == 0