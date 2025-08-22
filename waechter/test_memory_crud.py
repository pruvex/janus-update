import pytest
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from backend import crud
from datetime import datetime

# Eine separate In-Memory-Datenbank für Tests verwenden
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base hier für die Test-DB neu definieren
Base = declarative_base()

# --- SQLAlchemy Modelle für Chat-Historie (direkt hier definiert) ---
class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_archived = Column(Boolean, default=False)

    messages = relationship("Message", back_populates="chat")
    memories = relationship("Memory", back_populates="chat") # Hinzugefügt

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    sender = Column(String)
    content = Column(String)
    image_path = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")

class Memory(Base):
    __tablename__ = "memory"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    snippet = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    chat = relationship("Chat", back_populates="memories") # Hinzugefügt

# Pytest Fixture, um eine saubere DB-Sitzung für jeden Test bereitzustellen
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
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

    search_results_klaus = crud.search_memory_by_text(db_session, search_term="Klaus")
    assert len(search_results_klaus) == 1
    assert search_results_klaus[0].snippet == "Der Benutzer heißt Klaus."

    search_results_farbe = crud.search_memory_by_text(db_session, search_term="farbe")
    assert len(search_results_farbe) == 1
    assert "Blau" in search_results_farbe[0].snippet

    search_results_none = crud.search_memory_by_text(db_session, search_term="Berlin")
    assert len(search_results_none) == 0
